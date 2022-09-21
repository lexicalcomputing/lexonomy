#!/usr/bin/python3
# Copyright (c) 2019-2022 Lexical Computing: Miloš Jakubíček, Vojtěch Kovář, Marek Medveď, Jan Michelfeit
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import sys, re, os, fileinput
from urllib.parse import quote_plus
import hashlib

def get_filename(value, extension='.nvh'):
    enc_value = quote_plus(value)
    if len(enc_value) > 100:
        enc_value = hashlib.md5(value.encode('utf8')).hexdigest()
    return enc_value + extension


class nvh:
    def __init__ (self, parent, indent="", name="", value="", children = None):
        self.parent = parent
        self.name = name
        self.value = value
        self.indent = indent
        self.children = children or []

    def __repr__(self):
        return "%s: %s" % (self.name, self.value)

    def dump (self, out, do_projection = False):
        if hasattr(self, "do_projection"):
            delattr(self, "do_projection")
            return self.dump(out, True)
        if self.name:
            if self.parent and self.parent.parent and self.parent.parent.name:
                # force consistent indent
                ind_step = self.parent.indent[len(self.parent.parent.indent):]
                self.indent = self.parent.indent + ind_step
            elif self.parent and self.parent.name:
                self.indent = self.parent.children[0].indent
            out.write(self.indent + self.name + ": " + self.value + "\n")
        for c in self.children:
            project = getattr(c, "project", 0)
            if not do_projection or project:
                c.dump (out, project == 1)

    def filter_entries (self, selectors, projectors, maxitems=0):
        def prepare_selector(q):
            m = re.match("((?:[a-zA-Z._](?:#[<>=]+\d+)?)+) *(?:(=|!=|~=)(.*))?$", q)
            # e.g. 'hw.sense.example#=0.quality=bad'
            if not m:
                raise Exception("Invalid query: '%s'" % q)
            return m.groups()
        self.refresh()
        children = [c for c in self.children if all(c.selection(*prepare_selector(f)) for f in selectors)]
        if maxitems:
            children = children[:maxitems]
        d = nvh(self.parent, self.indent, self.name, self.value, children)
        if projectors:
            for p in projectors:
                d.prepare_projection(p)
            d.do_projection = True
        return d

    def refresh(self):
        if hasattr(self, 'selected'):
            delattr(self, 'selected')
        if hasattr(self, 'project'):
            delattr(self, 'project')
        if hasattr(self, "do_projection"):
            delattr(self, "do_projection")
        for c in self.children:
            c.refresh()

    def prepare_projection (self, q):
        out = False
        for c in self.children:
            if "." in q:
                name, qq = q.split(".", 1)
                if c.name == name and getattr(c, "selected", 1):
                    if c.prepare_projection(qq):
                        c.project = getattr(c, "project", 1)
                        out = True
            elif (c.name == q or c.name+'!' == q) \
                                            and getattr(c, "selected", 1):
                c.project = 2
                out = True
        if q.endswith('!') and not out:
            self.project = 0
        return out

    def selection (self, lhs, operator, rhs, mark_selected=1):
        is_selected = getattr(self, "selected", 1)
        if "." in lhs: # dive in
            name, new_lhs = lhs.split(".", 1)
            if "." in new_lhs:
                nextname, rest = new_lhs.split(".", 1)
                new_lhs = nextname.split("#")[0] + "." + rest
            else:
                nextname, rest = new_lhs, ''
                new_lhs = nextname.split("#")[0]
            if self.name != name:
                return False
            elif "#" in nextname: # count
                nextname, condition = nextname.split('#', 1)
                if condition.startswith('='):
                    condition = condition.replace("=", "==")
                new_mark_selected = 0
            else:
                new_mark_selected = 1
                condition = ">0"
            numof_children = len([c for c in self.children
                     if c.selection(new_lhs, operator, rhs, new_mark_selected)])
            if eval("%d%s" % (numof_children, condition)):
                if mark_selected: self.selected = is_selected
                return True
            else:
                if mark_selected: self.selected = 0
                return False
        elif self.name != lhs: # nothing, names don't match
            return False
        # now, it's guaranteed that self.name == lhs
        if operator == "!=":
            if self.value != rhs:
                if mark_selected: self.selected = is_selected
                return True
            if mark_selected: self.selected = 0
            return False
        if operator == "~=":
            if re.match(rhs, self.value):
                if mark_selected: self.selected = is_selected
                return True
            if mark_selected: self.selected = 0
            return False
        if operator == "=":
            if self.value == rhs:
                if mark_selected: self.selected = is_selected
                return True
            if mark_selected: self.selected = 0
            return False
        if mark_selected: self.selected = is_selected
        return True


    def merge (self, patch, replacers, print_counts=True):

        def new_replacers(replacers, childname):
            parsed_reps = [r.split(".", 1) for r in replacers if "." in r]
            return [r[1] for r in parsed_reps if childname == r[0]]

        from collections import defaultdict
        self_hash = defaultdict(list)
        for i, c in enumerate(self.children):
            self_hash[c.value].append(c)
        added = 0
        updated = 0
        processed_names = set()
        for pc in patch.children:
            if pc.name + '!' in replacers:
                self.children = [x for x in self.children
                             if x.name != pc.name or x.value != pc.value]
                continue
            if pc.name in replacers: # replacing existing records
                if pc.name in processed_names:
                    continue
                ii = len(self.children) # index where to put pc.name
                for i, c in enumerate(self.children):
                    if c.name == pc.name:
                        ii = i
                        break
                self.children = [x for x in self.children
                                       if x.name != pc.name]
                for pc2 in patch.children: # add all nodes with same name
                    if pc2.name == pc.name:
                        self.children.insert(ii, pc2)
                        ii += 1
                        pc2.parent = self
                processed_names.add(pc.name)
                updated += 1
                continue
            merged = False
            for c in self_hash[pc.value]:
                if c.value == pc.value and c.name == pc.name:
                    c.merge(pc, new_replacers(replacers, c.name), False)
                    merged = True
                    updated += 1
            if not merged: # find right place and insert
                ii = len(self.children)
                for i, c in enumerate(self.children):
                    if c.name == pc.name:
                        ii = i
                self.children.insert(ii+1, pc)
                pc.parent = self
                self_hash[pc.value].append(pc)
                added += 1
        for rep in replacers:
            if not '.' in rep and rep not in processed_names: # deleting
                self.children = [x for x in self.children if x.name != rep]
                updated += 1
        if print_counts:
            print("Added %d entries, updated %d entries" % (added, updated),
                  file=sys.stderr)

    def split (self, outdir):
        for c in self.children:
            outfile = open("%s/%s" % (outdir, get_filename(c.value)), "w")
            c.dump(outfile)

    def generate_schema (self, schema, firstParent = True):
        seen = {n: False for n in schema}
        firstInThisParent = {c.name: True for c in self.children}
        for c in self.children:
            is_this_new = firstInThisParent[c.name] and firstParent
            if c.name not in schema: # first occurrence across all parents
                schema[c.name] = {"optional": not firstParent, "repeated": False, "schema": {}}
                is_this_new = True
            elif not firstInThisParent[c.name]:
                schema[c.name]["repeated"] = True
            seen[c.name] = True
            c.generate_schema(schema[c.name]["schema"], is_this_new)
            firstInThisParent[c.name] = False
        for n in seen:
            if not seen[n]:
                schema[n]["optional"] = True

    def check_schema(self, schema, parent="ROOT", ancestor=None, outfile=sys.stdout):

        def report(s):
            outfile.write("ERROR: %s (%s)\n" % (s, ancestor))

        from collections import Counter
        keyval_freqs = Counter((c.name, c.value) for c in self.children)
        duplicates = [d for d in keyval_freqs.items() if d[1] > 1]
        for d in duplicates:
            report("Duplicate key-value pair '%s: %s' for parent %s (occurs %d times)" % (d[0][0], d[0][1], parent, d[1]))
        freqs = Counter(c.name for c in self.children)
        for n in freqs:
            if n not in schema:
                report("%s not allowed as a child of %s" % (n, parent))
                continue
            if freqs[n] > 1 and not schema[n]["repeated"]:
                report("%s not allowed to be repeated" % n)
        for n in schema:
            if not schema[n]["optional"] and not n in freqs:
                report("%s is mandatory and missing as child of %s" % (n, parent))

        for c in self.children:
            if c.name in schema:
                c.check_schema(schema[c.name]["schema"], c.name, ancestor or "%s: %s" % (c.name, c.value), outfile=outfile)


    def nvh2schema (self):
        schema = {}
        for c in self.children:
            if c.name in schema:
                raise Exception("Invalid schema: %s specified multiple times" % c.name)
            node_def = {}
            if c.value == "":
                node_def["optional"] = False
                node_def["repeated"] = False
            elif c.value == "?":
                node_def["optional"] = True
                node_def["repeated"] = False
            elif c.value == "+":
                node_def["optional"] = False
                node_def["repeated"] = True
            elif c.value == "*":
                node_def["optional"] = True
                node_def["repeated"] = True
            else:
                raise Exception("Invalid schema: %s has invalid value '%s'" % (c.name, c.value))
            node_def["schema"] = c.nvh2schema()
            schema[c.name] = node_def
        return schema

    @staticmethod
    def print_schema (s, indent = 0, outfile = sys.stdout):
        def get_symbol(d):
            if d["optional"]:
                if d["repeated"]:
                    return "*"
                return "?"
            elif d["repeated"]:
                return "+"
            return ""
        for k in s:
            print("%s%s: %s" % (" " * indent, k, get_symbol(s[k])), file=outfile)
            nvh.print_schema (s[k]["schema"], indent + 4, outfile)

    @staticmethod
    def parse_line (line, line_nr, parent):
        n, v = line.split(":", 1)
        indent = re.match("[ \t]+", n)
        if indent:
            i = indent.group(0)
            if " " in i and "\t" in i:
                raise Exception ("Mixing tabs and spaces on line %d" % line_nr)
            if (" " in i and "\t" in parent.indent) or ("\t" in i and " " in parent.indent):
                raise Exception ("Inconsistent indentation on line %d" % line_nr)
            indent = i
        else:
            indent = ""
        return indent, n.strip(), v.strip()

    @staticmethod
    def parse_file (infile):
        dictionary = nvh(None)
        curr_parent = dictionary
        line_nr = 0
        last_indent = ""
        for line in infile:
            line_nr += 1
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            indent, name, value = nvh.parse_line (line, line_nr, curr_parent)
            if indent > last_indent:
                curr_parent = curr_parent.children[-1]
            elif indent < last_indent:
                while indent != curr_parent.indent:
                    curr_parent = curr_parent.parent
                curr_parent = curr_parent.parent
            curr_parent.children.append(nvh(curr_parent, indent, name, value))
            last_indent = indent
        return dictionary

if __name__ == "__main__":
    def err(s):
        print(s, file=sys.stderr)

    def usage():
        err("Usage:")
        err("%s get DB [ SELECT_FILTER [ PROJECT_FILTER ]]" % sys.argv[0])
        err("%s put DB PATCH_DB [ REPLACE_FILTER ]" % sys.argv[0])
        err("%s split file.nvh OUTPUT_DIRECTORY" % sys.argv[0])
        err("%s genschema file.nvh" % sys.argv[0])
        err("%s checkschema file.nvh schema.nvh" % sys.argv[0])
        err("DB is a file in NVH format")
        err("FILTER is a dot-notated path to a name, multiple FILTERs can be comma-separated and are ANDed")
        err("SELECT_FILTER supports equality, non-equality, Python regexp testing and count (#)")
        err("Examples:")
        err("%s get file.nvh" % sys.argv[0])
        err("%s get file.nvh hw.sense hw.pos,hw.form" % sys.argv[0])
        err("%s get file.nvh hw.form=blaming hw.pos,hw.form" % sys.argv[0])
        err("%s get file.nvh hw.form!=blaming hw.pos,hw.form" % sys.argv[0])
        err("%s get file.nvh hw.form~=\"blam.*\" w.pos,hw.form" % sys.argv[0])
        err("%s get file.nvh 'hw.sense.example#=0' hw.sense" % sys.argv[0])
        err("%s get file.nvh 'hw.sense.example#>0.quality=bad' hw.sense" % sys.argv[0])
        err("%s put file.nvh patch.nvh hw.sense" % sys.argv[0])
        os._exit(1)

    if len(sys.argv) < 3:
        usage()

    try:
        infile = fileinput.input([sys.argv[2]])
        dictionary = nvh.parse_file(infile)
        if sys.argv[1].startswith("get"):
            select_filters = []
            project_filters = []
            maxitems = 0
            if len(sys.argv) > 3:
                select_filters = sys.argv[3].split(",")
                if select_filters[0].startswith('##'):
                    maxitems = int(select_filters[0][2:])
                    select_filters = select_filters[1:]
                if len(sys.argv) > 4:
                    project_filters = sys.argv[4].split(",")
            dictionary = dictionary.filter_entries(select_filters, project_filters, maxitems)
            dictionary.dump(sys.stdout)
        elif sys.argv[1] == "put":
            if len(sys.argv) < 4:
                usage()
            infile = fileinput.input([sys.argv[3]])
            patch = nvh.parse_file(infile)
            if len(sys.argv) > 4:
                replace_filters = sys.argv[4].split(",")
            else:
                replace_filters = []
            dictionary.merge(patch, replace_filters)
            dictionary.dump(sys.stdout)
        elif sys.argv[1] == "split":
            if len(sys.argv) < 4:
                usage()
            outdir = sys.argv[3]
            if not os.path.isdir(outdir):
                err("Argument '%s' should be a directory" % outdir)
                usage()
            dictionary.split(outdir)
        elif sys.argv[1] == "genschema":
            schema = {}
            dictionary.generate_schema(schema)
            nvh.print_schema (schema)
        elif sys.argv[1] == "checkschema":
            if len(sys.argv) < 4:
                usage()
            infile = fileinput.input([sys.argv[3]])
            schema = nvh.parse_file(infile)
            schema = schema.nvh2schema()
            dictionary.check_schema(schema)
        else:
            usage()
    except:
        err("Error processing file '%s' at line %d" % (infile.filename(), infile.filelineno()))
        raise
