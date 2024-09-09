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
from log_subprocess import log_err, log_info, log_warning, log_end, log_start

current_dir = os.path.dirname(os.path.realpath(__file__))

def purge_dict(db, historiography, purge_all, email):
    if purge_all:
        log_info("Purging history...")
        db.execute("delete from history")
    else:
        log_info("Copying all entries to history...")
        db.execute("INSERT INTO history(entry_id, action, [when], email, nvh, historiography) "
                   "SELECT id, 'purge', ?, ?, nvh, ? from entries",
                   (str(datetime.datetime.utcnow()), email, json.dumps(historiography)))
        
    log_info("Purging entries...")
    db.execute("delete from entries")
    db.execute("delete from linkables")
    db.execute("delete from searchables")
    db.execute("UPDATE configs SET json=? WHERE id=?", (0, 'entry_count'))
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
                nvh_element = '{}{}: {}\n'.format('  '*indent if indent else '', ch.tagName, re.sub('[ \n\r]+', ' ', ch.firstChild.nodeValue.strip()))
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
                        nvh_element = '{}{}: {}\n'.format('  '*indent if indent else '', ch.tagName, re.sub('[ \n\r]+', ' ', ch.attributes.items()[0][1].strip()))
                else:
                    if ch.attributes.length > 1 and (ch.tagName not in reported):
                        log_warning(f'Only one attribute allowed in XML item. {str(ch.tagName)}. Processing the first one.')
                        reported.add(ch.tagName)
                    nvh_element = '{}{}: {}\n'.format('  '*indent if indent else '', ch.tagName, re.sub('[ \n\r]+', ' ', ch.attributes.items()[0][1].strip()))
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
            log_info("XML2NVH: PER:%.2d, COUNT:%d/%d" % ((entry_processed/entryCount*100), entry_processed, entryCount))

    log_info("XML2NVH: PER:%.2d, COUNT:%d/%d" % ((entry_processed/entryCount*100), entry_processed, entryCount))


def import_configs(db, dict_id, config_data):
    for key, value in config_data.items():
        ops.updateDictConfig(db, dict_id, key, value)
    curr_configs = ops.readDictConfigs(db)
    ops.resave(db, dict_id, curr_configs)


def import_data(dbname, filename, email='IMPORT@LEXONOMY', main_node_name='', purge=False, purge_all=False, deduplicate=False, clean=False, config_data=''):
    log_start('IMPORT')
    log_info(f'pid: {str(os.getpid())}')

    dict_id = dbname.strip().split('/')[-1][:-7]
    log_info('IMPORTING (%s)' % (dict_id))
    db = None

    try:
        # =============
        # Load data
        # =============
        if filename.endswith('.xml'):
            log_info('XML to NVH processing')
            with open(filename + ".xml2nvh.nvh", 'w') as f:
                xml2nvh(filename, f)
            import_nvh = nvh.parse_file(fileinput.input(filename + ".xml2nvh.nvh"))

        elif filename.endswith('.nvh') or filename.endswith('.in'):
            import_nvh = nvh.parse_file(fileinput.input(filename))

        else:
            log_err(f'NOT a supported format: {filename}')
            sys.exit()
        # =============

        # =============
        ## Cleaning duplicate (name, value) nodes
        # =============
        if deduplicate:
            log_info('Cleaning NVH')
            import_nvh.clean_duplicate_nodes(out=sys.stderr)

        # =============
        ## Renaming node names that appear under different parents
        # =============
        rename_dict = {}
        name_mapping = {}
        if clean:
            log_info('Renaming duplicate NVH nodes')
            import_nvh.rename_nodes(rename_dict, out=sys.stderr)

            with open(filename + ".cleaned", 'w') as clean_f:
                import_nvh.dump(clean_f)

            for orig_name, rename_list in rename_dict.items():
                for _, new_name in rename_list:
                    name_mapping[new_name] = orig_name

        # =============
        # Generating schema form NVH
        # =============
        log_info('Generating schema')
        schema = {}
        import_nvh.generate_schema(schema, tln=True)
        with open(filename + ".schema", 'w') as schema_f:
            nvh.print_schema(schema, outfile=schema_f)

        #import_nvh.check_schema(schema, outfile=sys.stderr)

        # =============
        # Splitting into individual entries
        # =============
        import_entries, tl_node_names, tl_node_contains_pos = import_nvh.get_entries()
        del import_nvh

        if len(tl_node_names) == 1:
            tl_name = tl_node_names.pop()
        else:
            log_err(f'Only one top level name is supported. {list(tl_node_names)} found.')
            raise Exception('Too many top lavel names')
        entry_count = len(import_entries)

        # =============
        # Configuring dict
        # =============
        historiography={"importStart": str(datetime.datetime.utcnow()), "filename": os.path.basename(filename)}

        db = sqlite3.connect(dbname)
        db.row_factory = sqlite3.Row
        if purge or purge_all:
            purge_dict(db, historiography, purge_all, email)

        # =============
        # Structure
        # =============
        elements = {}
        ops.get_gen_schema_elements(schema, elements)
        structure = {"root": main_node_name, "elements": elements}
        if purge_all:
            db.execute("INSERT OR REPLACE INTO configs (id, json) VALUES (?, ?)", ("structure", json.dumps(structure)))
            db.execute("INSERT OR REPLACE INTO configs (id, json) VALUES (?, ?)", ("name_mapping", json.dumps(name_mapping)))
        else:
            c0 = db.execute("SELECT json FROM configs WHERE id=?", ("structure",))
            r0 = c0.fetchone()
            if r0:
                if json.dumps(structure) != r0['json']:
                    log_warning('Old structure is not compatible with new data. Use "Purge All" option')

            db.execute("INSERT OR IGNORE INTO configs (id, json) VALUES (?, ?)", ("structure", json.dumps(structure)))
            db.execute("INSERT OR IGNORE INTO configs (id, json) VALUES (?, ?)", ("name_mapping", json.dumps(name_mapping)))


        # =============
        # Formatting
        # =============
        formatting = {}
        with open(current_dir + "/dictTemplates/styles.json", 'r') as f:
            styles = json.loads(f.read())
            for key in elements.keys():
                if styles.get(key):
                    formatting[key] = styles[key]
                else:
                    formatting[key] = styles['__other__']

        if purge_all:
            db.execute("INSERT OR REPLACE INTO configs (id, json) VALUES (?, ?)", ("formatting", json.dumps(formatting)))
        else:
            db.execute("INSERT OR IGNORE INTO configs (id, json) VALUES (?, ?)", ("formatting", json.dumps(formatting)))

        configs = ops.readDictConfigs(db)
        dict_stats = ops.getDictStats(db)

        main_db = ops.getMainDB()
        log_info(f"Importing {filename} into {dict_id}")
        d = main_db.execute("SELECT configs FROM dicts WHERE id=?", (dict_id,))
        limit = int(json.loads(d.fetchone()['configs'])['limits']['entries'])

        # =============
        # Limits
        # =============
        max_import = limit - dict_stats["entryCount"]
        if max_import < entry_count:
            log_warning("Detected %d entries in '%s' element, only %d will be imported." % (entry_count, tl_name, max_import))
        else:
            log_info("Detected %d entries in '%s' element" % (entry_count, tl_name))

        # =============
        # Inserting new items
        # =============
        needs_refac = 0
        needs_resave = 1 if configs["searchability"].get("searchableElements") and len(configs["searchability"].get("searchableElements")) > 0 else 0
        cut_pos_re = re.compile('(.*)-.*')
        entries_insert_payload = []
        entries_update_payload = []
        searchables_payload = []
        history_payload = []
        searchables_delete_payload = []

        entries_inserted = 0
        completed_entries = 0

        # max entry id form DB is exists
        max_entryID = db.execute("SELECT MAX(id) AS max_ID FROM entries").fetchone()['max_ID']
        if max_entryID:
            entryID = int(max_entryID)
        else:
            entryID = 0

        entry_inserted = 0
        limit_reached = False

        while import_entries:
            entry = import_entries.pop(0)
            entry_str = entry.dump_string()
            entry_json = ops.nvh2json(entry)

            if entry_inserted >= max_import:
                limit_reached = True
                break

            action = "create"
            entry_key = ops.getEntryHeadword(entry, main_node_name)
            searchTitle = ops.getEntryTitle(entry, configs["titling"], True)
            title = "<span class='headword'>" + entry_key + "</span>"

            # ========================
            # UPDATE OR INSERT
            # ========================
            c = db.execute("SELECT id, nvh FROM entries WHERE sortkey=?", (entry_key,))
            r = c.fetchone()

            if not r:
                entryID += 1
                entries_insert_payload.append((entryID, entry_str, entry_json, needs_refac, needs_resave, 0, tl_name, title, entry_key))
                history_payload.append((entryID, action, str(datetime.datetime.utcnow()), email, entry_str, json.dumps(historiography)))
                searchables_payload.append((entryID, searchTitle, 1))
                if tl_node_contains_pos:
                    searchTitle_no_pos = cut_pos_re.match(searchTitle).group(1)
                    searchables_payload.append((entryID, searchTitle_no_pos, 1))

                if '__lexonomy__completed' in entry_str:
                    completed_entries += 1
                entries_inserted += 1

            # Updating existing
            else:
                action = "update"
                entries_update_payload.append((entry_str, entry_json, needs_refac, needs_resave, 0, tl_name, title, entry_key, r["id"]))
                history_payload.append((r["id"], action, str(datetime.datetime.utcnow()), email, entry_str, json.dumps(historiography)))
                searchables_delete_payload.append((r['id'], 1))
                searchables_payload.append((r["id"], searchTitle, 1))
                if tl_node_contains_pos:
                    searchTitle_no_pos = cut_pos_re.match(searchTitle).group(1)
                    searchables_payload.append((r["id"], searchTitle_no_pos, 1))

                if '__lexonomy__completed' in entry_str and '__lexonomy__completed' not in r['nvh']:
                    completed_entries += 1

            entry_inserted += 1

            if entry_inserted % 100 == 0:
                log_info("IMPORTED: PER:%.2d, COUNT:%d/%d" % ((entry_inserted/entry_count*100), entry_inserted, entry_count))

        if limit_reached:
            log_info("IMPORTED (%s): PER:100, COUNT:%d/%d, MSG:Entry limit was reached. To remove the limit, " \
                    "email inquiries@sketchengine.eu and give details of your dictionary project." % (dict_id, entry_inserted, entry_count))
        else:
            log_info("IMPORTED (%s): PER:100, COUNT:%d/%d"  % (dict_id, entry_inserted, entry_count))

        db.executemany("INSERT INTO entries(id, nvh, json, needs_refac, needs_resave, needs_refresh, doctype, title, sortkey) VALUES (?,?,?,?,?,?,?,?,?)", entries_insert_payload)
        db.executemany("UPDATE entries SET nvh=?, json=?, needs_refac=?, needs_resave=?, needs_refresh=?, doctype=?, title=?, sortkey=? WHERE id=?", entries_update_payload)
        db.executemany("INSERT INTO history(entry_id, action, [when], email, nvh, historiography) VALUES (?,?,?,?,?,?)", history_payload)
        db.executemany("DELETE FROM searchables WHERE entry_id=? and level=?", searchables_delete_payload)
        db.executemany("INSERT INTO searchables(entry_id, txt, level) VALUES (?, ?, ?)", searchables_payload)

        # =============
        # Entry counts
        # =============
        c2 = db.execute("SELECT json FROM configs WHERE id='entry_count'")
        r2 = c2.fetchone()
        if r2:
            db.execute("UPDATE configs SET json=? WHERE id=?", (int(r2['json']) + entries_inserted, 'entry_count'))

        c3 = db.execute("SELECT json FROM configs WHERE id='completed_entries'")
        r3 = c3.fetchone()
        if r3:
            db.execute("UPDATE configs SET json=? WHERE id=?", (int(r3['json']) + completed_entries, 'completed_entries'))

        # =============
        # Import config
        # =============
        if config_data:
            import_configs(db, dict_id, config_data)

        db.commit()

    except Exception as e:
        log_err(f"Import crashed on: {e}")

    if db:
        db.close()

    log_end("IMPORT")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import entries from NVH into Lexonomy SQLite database')
    parser.add_argument('dbname', type=str,
                        help='path to DB sqlite file')
    parser.add_argument('filename', type=str,
                        help='path to importing file')
    parser.add_argument('email', type=str,
                        default='IMPORT@LEXONOMY', help='user email')
    parser.add_argument('main_node_name', type=str, default='',
                        help='Name of the mani node of the entry (headword, entry, ...)')
    parser.add_argument('-p', '--purge', action='store_true',
                        required=False, default=False,
                        help='Backup and purge dictionary history')
    parser.add_argument('-pp', '--purge_all', action='store_true',
                        required=False, default=False,
                        help='Purge dictionary with history and all configs without backup')
    parser.add_argument('-d', '--deduplicate', action='store_true',
                        required=False, default=False,
                        help='Deduplicate nodes with same name and value on the same level')
    parser.add_argument('-c', '--clean', action='store_true',
                        required=False, default=False,
                        help='Renaming node names that appear under different parents')
    parser.add_argument('--config', type=str,
                        required=False, default='',
                        help='Dictionary config in JSON format')
    args = parser.parse_args()

    config_json = None
    if args.config:
        with open(args.config) as f:
            config_json = json.load(f)

    import_data(args.dbname, args.filename, args.email, args.main_node_name, args.purge, args.purge_all, args.deduplicate, args.clean, config_data=config_json)


if __name__ == '__main__':
    main()
