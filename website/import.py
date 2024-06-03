#!/usr/bin/python3.10
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import re
import ops
import sys
import json
import sqlite3
import datetime
import fileinput
import xml.sax
import xml.dom.minidom
from nvh import nvh
current_dir = os.path.dirname(os.path.realpath(__file__))

def log_info(msg):
    sys.stderr.write(f'INFO: {msg}\n')


def log_err(msg):
    sys.stderr.write(f'ERROR: {msg}\n')


def log_warning(msg):
    sys.stderr.write(f'WARNING: {msg}\n')


def purge(db, historiography, args):
    if args.purge_all:
        log_info("Purging history...")
        db.execute("delete from history")
    else:
        log_info("Copying all entries to history...")
        db.execute("INSERT INTO history(entry_id, action, [when], email, nvh, historiography) "
                   "SELECT id, 'purge', ?, ?, nvh, ? from entries",
                   (str(datetime.datetime.utcnow()), args.email, json.dumps(historiography)))
        
    log_info("Purging entries...")
    db.execute("delete from entries")
    db.execute("delete from linkables")
    db.execute("delete from searchables")
    db.commit()

    log_info("Compressing database...")
    db.execute("vacuum")
    db.commit()

rootTag = ''
entryTag = ''
entryCount = 0
class handlerFirst(xml.sax.ContentHandler):
    def startElement(self, name, attrs):
        """
        Fist element in XML is root tag
        and the second element is entry tag
        """
        global rootTag
        global entryTag
        if rootTag == "":
            rootTag = name
        elif entryTag == "":
            entryTag = name
        else:
            pass

    def endElement(self, name):
        global entryCount
        global entryTag
        if name == entryTag:
            entryCount += 1

def xml_entry2nvh_entry(dom, fd, indent=0, idx=0, reported=set()):
    """
    Transforming the XML entry into NVH entry
    """
    for ch in dom.childNodes:
        nvh_element = ''
        if not isinstance(ch, xml.dom.minidom.Text):
            if isinstance(ch.firstChild, xml.dom.minidom.Text) and ch.firstChild.nodeValue.strip():
                # content in tag value
                nvh_element = '{}{}: {}\n'.format('  '*indent if indent else '', ch.tagName, re.sub('[ \n]+', ' ', ch.firstChild.nodeValue.strip()))
            elif ch.attributes.length > 0:
                # content in tag attribute
                if entryTag == ch.tagName:
                    if ch.attributes.length > 1 and (ch.tagName not in reported):
                        log_warning(f'The XML tag <{ch.tagName}> should contain only one attribute. *ID* attribute will be provided as value, the rest will be as added children.')
                        reported.add(ch.tagName)
                    for attr_name, attr_val in ch.attributes.items():
                        if re.search('id', attr_name, re.IGNORECASE):
                            nvh_element = '{}{}: {}\n'.format('  '*indent if indent else '', ch.tagName, attr_val)

                    for attr_name, attr_val in ch.attributes.items():
                        nvh_element += '{}xtag({}): {}\n'.format('  '*indent+1 if indent else '  ', re.sub(':', '~', attr_name), attr_val)

                    if not nvh_element:
                        if ch.attributes.length > 1 and (ch.tagName not in reported):
                            log_warning(f'Only one attribute allowed in XML item. {str(ch.tagName)}. Processing the first one.')
                            reported.add(ch.tagName)
                        nvh_element = '{}{}: {}\n'.format('  '*indent if indent else '', ch.tagName, re.sub('[ \n]+', ' ', ch.attributes.items()[0][1].strip()))
                else:
                    if ch.attributes.length > 1 and (ch.tagName not in reported):
                        log_warning(f'Only one attribute allowed in XML item. {str(ch.tagName)}. Processing the first one.')
                        reported.add(ch.tagName)
                    nvh_element = '{}{}: {}\n'.format('  '*indent if indent else '', ch.tagName, re.sub('[ \n]+', ' ', ch.attributes.items()[0][1].strip()))
            else:
                # wrapper without value
                if entryTag == ch.tagName:
                    nvh_element = '{}{}: {}\n'.format('  '*indent if indent else '', ch.tagName, idx)
                    idx += 1
                else:
                    nvh_element = '{}{}:\n'.format('  '*indent if indent else '', ch.tagName)
            fd.write(nvh_element)

        xml_entry2nvh_entry(ch, fd, indent + 1, idx, reported=reported)


def xml2nvh(input_xml , fd):
    global rootTag
    global entryTag
    global entryCount
    with open(input_xml, 'rb') as f:
        xmldata = f.read().decode('utf-8-sig')
    xmldata = re.sub(r'<\?xml[^?]*\?>', '', xmldata)
    xmldata = re.sub(r'<!DOCTYPE[^>]*>', '', xmldata)
    xmldata = re.sub(r'</?b>', '', xmldata)
    xmldata = re.sub(r'</?p>', '', xmldata)
    xmldata = re.sub(r'</?i>', '', xmldata)
    entry_processed = 0

    # Parsing xml and finding the root tag and the entry tag
    try:
        xml.sax.parseString("<!DOCTYPE foo SYSTEM 'x.dtd'>\n"+xmldata, handlerFirst())
        xmldata = "<!DOCTYPE foo SYSTEM 'x.dtd'>\n"+xmldata
    except xml.sax._exceptions.SAXParseException as e:
        if "junk after document element" in str(e):
            xmldata = "<!DOCTYPE foo SYSTEM 'x.dtd'>\n<fakeroot>"+xmldata+"</fakeroot>"
            rootTag = ""
            entryTag = ""
            entryCount = 0
            xml.sax.parseString(xmldata, handlerFirst())
        else:
            if entryTag == "":
                log_err("Not possible to detect element name for entry, please fix errors")

    re_entry = re.compile(r'<'+entryTag+'[^>]*>.*?</'+entryTag+'>', re.MULTILINE|re.DOTALL|re.UNICODE)
    for entry in re.findall(re_entry, xmldata):
        try:
            # Check if the entry is ok
            xml.sax.parseString(entry, xml.sax.handler.ContentHandler())
        except xml.sax._exceptions.SAXParseException as e:
            log_err("Skipping entry, XML parsing error: " + str(e))
            log_err("Entry with error: " + entry)

        xml_entry2nvh_entry(xml.dom.minidom.parseString(entry), fd)

        entry_processed += 1
        if entry_processed % 100 == 0:
            log_info("DONE_XML2NVH: PER:%.2d, COUNT:%d/%d" % ((entry_processed/entryCount*100), entry_processed, entryCount))

    log_info("DONE_XML2NVH: PER:%.2d, COUNT:%d/%d" % ((entry_processed/entryCount*100), entry_processed, entryCount))


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import entries from NVH into Lexonomy SQLite database')
    parser.add_argument('dbname', type=str, 
                        help='database file name')
    parser.add_argument('filename', type=str, 
                        help='import file name')
    parser.add_argument('email', type=str,
                        default='IMPORT@LEXONOMY', help='user email')
    parser.add_argument('main_node_name', type=str, default='',
                        help='Name of the mani node of the entry (headword, entry, ...)')
    parser.add_argument('-p', '--purge', action='store_true',
                        required=False, default=False,
                        help='Backup and purge dictionary history')
    parser.add_argument('-pp', '--purge_all', action='store_true',
                        required=False, default=False,
                        help='Purge dictionary history without backup')
    parser.add_argument('-d', '--deduplicate', action='store_true',
                        required=False, default=False,
                        help='Deduplicate nodes with same name and value on the same level')

    args = parser.parse_args()

    sys.stderr.write(f'PID: {str(os.getpid())}\n')
    log_info("Import started. You may close the window, import will run in the background. Please wait...")

    try:
        if args.filename.endswith('.xml'):
            log_info('XML to NVH processing')
            with open(args.filename + ".xml2nvh.nvh", 'w') as f:
                xml2nvh(args.filename, f)
            import_nvh = nvh.parse_file(fileinput.input(args.filename + ".xml2nvh.nvh"))

        elif args.filename.endswith('.nvh') or args.filename.endswith('.in'):
            import_nvh = nvh.parse_file(fileinput.input(args.filename))

        else:
            log_err(f'NOT a supported format: {args.filename}')
            sys.exit()

        ## Cleaning duplicate (name, value) nodes
        if args.deduplicate:
            log_info('Cleaning NVH')
            import_nvh.clean_duplicate_nodes(out=sys.stderr)

        ## Renaming node names that appear under different parents
        log_info('Renaming duplicate NVH nodes')
        rename_dict = {}
        import_nvh.rename_nodes(rename_dict, out=sys.stderr)

        with open(args.filename + ".cleaned", 'w') as clean_f:
            import_nvh.dump(clean_f)

        name_mapping = {}
        for orig_name, rename_list in rename_dict.items():
            for _, new_name in rename_list:
                name_mapping[new_name] = orig_name

        # Generating schema form NVH
        schema = {}
        import_nvh.generate_schema(schema, tln=True)
        with open(args.filename + ".schema", 'w') as schema_f:
            nvh.print_schema(schema, outfile=schema_f)

        #import_nvh.check_schema(schema, outfile=sys.stderr)

        # Splitting into individual entries
        import_entries, tl_node_names, tl_node_contains_pos = import_nvh.get_entries()
        if len(tl_node_names) == 1:
            tl_name = tl_node_names.pop()
        else:
            log_err(f'Only one top level name is supported. {list(tl_node_names)} found.')
            raise Exception('Too many top lavel names')
        entry_count = len(import_entries)

        entry_inserted = 0
        limit_reached = False

        historiography={"importStart": str(datetime.datetime.utcnow()), "filename": os.path.basename(args.filename)}

        db = sqlite3.connect(args.dbname)
        db.row_factory = sqlite3.Row
        if args.purge:
            purge(db, historiography, args)

        elements = {}
        ops.get_gen_schema_elements(schema, elements)
        structure = {"root": args.main_node_name, "elements": elements}
        db.execute("INSERT OR REPLACE INTO configs (id, json) VALUES (?, ?)", ("structure", json.dumps(structure))) # TODO should be INSERT or IGNORE if exists
        db.execute("INSERT OR REPLACE INTO configs (id, json) VALUES (?, ?)", ("name_mapping", json.dumps(name_mapping)))

        formatting = {}
        with open(current_dir + "/dictTemplates/styles.json", 'r') as f:
            styles = json.loads(f.read())
            for key in elements.keys():
                if styles.get(key):
                    formatting[key] = styles[key]
                else:
                    formatting[key] = styles['__other__']
        db.execute("INSERT OR REPLACE INTO configs (id, json) VALUES (?, ?)", ("formatting", json.dumps(formatting)))

        configs = ops.readDictConfigs(db)
        dict_stats = ops.getDictStats(db)

        main_db = ops.getMainDB()
        dict_name = args.dbname.strip().split('/')[-1][:-7]
        log_info(f"Marek: {dict_name}")
        d = main_db.execute("SELECT configs FROM dicts WHERE id=?", (dict_name,))
        limit = int(json.loads(d.fetchone()['configs'])['limits']['entries'])

        max_import = limit - dict_stats["entryCount"]
        if max_import < entry_count:
            log_info("Detected %d entries in '%s' element, only %d will be imported." % (entry_count, tl_name, max_import))
        else:
            log_info("Detected %d entries in '%s' element" % (entry_count, tl_name))

        needs_refac = 0
        needs_resave = 1 if configs["searchability"].get("searchableElements") and len(configs["searchability"].get("searchableElements")) > 0 else 0

        log_info('Importing into dictionary')
        cut_pos_re = re.compile('(.*)-.*')
        for entry in import_entries:
            entry_str = entry.dump_string()
            if entry_inserted >= max_import:
                limit_reached = True
                break
            action = "create"
            entry_key = ops.getEntryHeadword(entry, args.main_node_name)
            title = "<span class='headword'>" + entry_key + "</span>"
            c = db.execute("SELECT id FROM entries WHERE sortkey=?", (entry_key,))
            r = c.fetchone()

            if not r:
                sql = "INSERT INTO entries(nvh, json, needs_refac, needs_resave, needs_refresh, doctype, title, sortkey) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                params = (entry_str, ops.nvh2json(entry), needs_refac, needs_resave, 0, tl_name, title, entry_key)

            else:
                sql = "UPDATE entries SET nvh=?, json=?, needs_refac=?, needs_resave=?, needs_refresh=?, doctype=?, title=?, sortkey=? WHERE id=?"
                params = (entry_str, ops.nvh2json(entry), needs_refac, needs_resave, 0, tl_name, title, entry_key, r["id"])
                action = "update"
            c = db.execute(sql, params)
            entryID = c.lastrowid
            db.execute("INSERT INTO history(entry_id, action, [when], email, nvh, historiography) VALUES (?, ?, ?, ?, ?, ?)",
                    (entryID, action, str(datetime.datetime.utcnow()), args.email, entry_str, json.dumps(historiography)))
            db.execute("DELETE FROM searchables WHERE entry_id=? and level=?", (entryID, 1))
            searchTitle = ops.getEntryTitle(entry, configs["titling"], True)
            db.execute("INSERT INTO searchables(entry_id, txt, level) VALUES (?, ?, ?)", (entryID, searchTitle, 1))
            if tl_node_contains_pos:
                searchTitle_no_pos = cut_pos_re.match(searchTitle).group(1)
                db.execute("INSERT INTO searchables(entry_id, txt, level) VALUES (?, ?, ?)", (entryID, searchTitle_no_pos, 1))
            entry_inserted += 1

            if entry_inserted % 100 == 0:
                log_info("DONE_IMPORT: PER:%.2d, COUNT:%d/%d" % ((entry_inserted/entry_count*100), entry_inserted, entry_count))

        if limit_reached:
            log_info("DONE_IMPORT: PER:100, COUNT:%d/%d, MSG:Entry limit was reached. To remove the limit, " \
                    "email inquiries@sketchengine.eu and give details of your dictionary project." % (entry_inserted, entry_count))

        log_info("DONE_IMPORT: PER:100, COUNT:%d/%d"  % (entry_inserted, entry_count))
        db.commit()
    except Exception as e:
        log_err(f"Import crashed on: {e}")


if __name__ == '__main__':
    main()
