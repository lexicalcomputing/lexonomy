DICT_DIR=./dicts
LEXONOMY_DICT_DIR=$(shell jq -r '.dataDir' ../../siteconfig.json)
MAIN_DB=lexonomy.sqlite

# ===============================================
migration: dump_xml dump_json migrate_data

lexonomy_public_dicts.csv:
	./scripts/public_dicts.py -d $(DICT_DIR) | grep -v "Diccionariodigitalciencias12" | \
                                               grep -v "xmedved1" | \
                                               grep -v "wvhysig3" | \
                                               grep -v "pchpt8qm" | \
                                               grep -v "qhxit8y3" | \
                                               grep -v "qvkvis65" | \
                                               grep -v "wvhysig3" | \
                                               grep -v "6kue332v" | \
                                               grep -v "cf4bmykh" | \
                                               grep -v "QaamuuskaAfaqoonta" | \
                                               grep -v "ubc3g8e9" | \
                                               grep -v "xme33n2b" | \
                                               grep -v "paroleletteratura" | \
                                               grep -v "pbff9vy2" | \
                                               grep -v "Nederlands" | \
                                               grep -v "k2htc6m8" | \
                                               grep -v "rilpoc" | \
                                               grep -v "zrx2byi5e" | \
                                               grep -v "t8wryugt" | \
                                               grep -v "bh2pfmtv" | \
                                               grep -v "hypolexicon" | \
                                               grep -v "neue-deutsche-sprache" | \
                                               grep -v "9c7dxj2i" | \
                                               grep -v "Qaamuuskaafsoomaaliga" | \
                                               grep -v "ijmgfq3s" | \
                                               grep -v "4k2mf3n3" | \
                                               grep -v "h8ee85wc" | \
                                               grep -v "qrinjxtc" | \
                                               grep -v "cyx36tp9" | \
                                               grep -v "QaamuuskaEraybixinta" | \
                                               grep -v "pswry5ew" | \
                                               grep -v "ssssyakobchuk" | \
                                               grep -v "iix8hh2e" | \
                                               grep -v "ife3b2kv" | \
                                               grep -v "t6xv3hs9" | \
                                               grep -v "KamusVerbeShintya" | \
                                               grep -v "paraleli" > $@

lexonomy_public_dicts_info.csv: lexonomy_public_dicts.csv
	cat $< | ./scripts/get_headword_node.py -d $(DICT_DIR) -f hw_fixes.csv > $@

dump_xml: lexonomy_public_dicts.csv
	mkdir $@
	for i in `cat $<`; do echo "Exporting $$i"; ./scripts/export.py $(DICT_DIR)/$$i.sqlite > ./dump_xml/$$i.xml; done
	sed -i 's/lxnm:Entry/Entry/g' $@/en-ua-eu_terms-dict_lab-soc-economics.xml
	cat dump_xml/gsldict.xml | ./scripts/replace.py '<sense></sense>\n\s*</cit>' '<sense>' > /tmp/gsldict.xml; mv /tmp/gsldict.xml dump_xml/gsldict.xml
	cat dump_xml/ztxs64ixt.xml | ./scripts/replace.py '<Origins><origin></Origins>' '' > /tmp/ztxs64ixt.xml; mv /tmp/ztxs64ixt.xml dump_xml/ztxs64ixt.xml
	cat dump_xml/2eb8hmh5.xml | ./scripts/replace.py '< licence' '<image licence' | ./scripts/replace.py '</>' '</image>' > /tmp/2eb8hmh5.xml; mv /tmp/2eb8hmh5.xml dump_xml/2eb8hmh5.xml
	cat dump_xml/ztxs64ixt.xml | ./scripts/replace.py '<entry' '<Entry' | ./scripts/replace.py '</entry>' '</Entry>' > /tmp/ztxs64ixt.xml; mv /tmp/ztxs64ixt.xml dump_xml/ztxs64ixt.xml
	cat dump_xml/archaeo-term.xml | ./scripts/replace.py '"<definition' '<definition' | ./scripts/replace.py '</definition>"' '</definition>' | ./scripts/replace.py '"<source>' '<source>' | ./scripts/replace.py '</source>"' '</source>' > /tmp/archaeo-term.xml; mv /tmp/archaeo-term.xml dump_xml/archaeo-term.xml
	sed -i 's/&amp;/\&/g' $@/elexis_dutch.xml
	cat dump_xml/marketing237ML2.xml | grep -v "^<office:meta>" > /tmp/marketing237ML2.xml; mv /tmp/marketing237ML2.xml dump_xml/marketing237ML2.xml
	cat dump_xml/gije7wrt.xml | grep -v "^<office:meta>" > /tmp/gije7wrt.xml; mv /tmp/gije7wrt.xml dump_xml/gije7wrt.xml
	cat dump_xml/ve8mfmh8.xml | grep -v "^<office:meta>" > /tmp/ve8mfmh8.xml; mv /tmp/ve8mfmh8.xml dump_xml/ve8mfmh8.xml
	cat dump_xml/dig2023.xml | grep -v "<entry>" > /tmp/dig2023.xml; mv /tmp/dig2023.xml dump_xml/dig2023.xml

dump_json: lexonomy_public_dicts.csv
	mkdir $@
	cat $< | ./scripts/export_config.py -d ${DICT_DIR} -o $@

user_credentials.csv:
	sqlite3 $(MAIN_DB) ".mode csv" "SELECT * FROM users" ".exit" > $@

XML=$(wildcard dump_xml/*.xml)
migrate_data: user_credentials.csv lexonomy_public_dicts_info.csv $(XML:%.xml=%.xml.xml2nvh.nvh)

%.xml.xml2nvh.nvh: %.xml
	grep $(subst dump_xml/,,$^) lexonomy_public_dicts_info.csv | python3.10 ./scripts/import_data.py ./dump_xml ./dump_json $(LEXONOMY_DICT_DIR) -c user_credentials.csv &> $@.log


clean_migration:
	for i in `find ./dump_xml/ -type f -name "*.xml"`; do ../delete.py "$${i:11:-4}"; done
	rm dump_xml/*.nvh dump_xml/*.schema dump_json/*.json

clean: clean_migration
	rm -rf dump_xml 
	rm -rf dump_json 
	rm user_credentials.csv 
	rm lexonomy_public_dicts.csv 
	rm lexonomy_public_dicts_info.csv
	
# ====================================================
# =================== STATS ==========================
# ====================================================
stats: lexonomy_last_access.csv lexonomy_last_edit.csv lexonomy_public_last_access.csv lexonomy_public_dict_sizes.csv

lexonomy_last_access.csv:
	./scripts/dict_last_access.py -d lexonomy.sqlite -p dicts

lexonomy_last_edit.csv:
	./scripts/dict_last_edit.py -d lexonomy.sqlite -p dicts

lexonomy_public_last_access.csv:
	cat lexonomy_public_dicts.log_pre4 | ./scripts/public_dict_last_access.py -d lexonomy_public_dicts.csv

lexonomy_public_dict_sizes.csv: lexonomy_public_dicts.csv
	cat $< | ./scripts/public_dict_size.py -p ${LEXONOMY_DICT_DIR} > $@
	#cat lexonomy_public_dicts.log_pre4 | ./scripts/public_dict_last_access_with_size.py -d lexonomy_public_dicts.csv -p dicts

clean_stats:
	rm -rf lexonomy_last_access.csv lexonomy_last_access.png lexonomy_last_edit.csv lexonomy_last_edit.png lexonomy_public_last_access.csv lexonomy_public_last_access.png lexonomy_public_dict_sizes.csv lexonomy_public_dict_sizes.png

# ====================================================
# =================== UTILS ==========================
# ====================================================
check_result:
	cat lexonomy_public_dicts_info.csv | sed "s/	/,/g" > lexonomy_public_dicts_info.csv.comma
	while IFS=, read -r xml dict hw lang note; do echo "=============================="; echo "$$xml, $$dict, $$hw, $$note"; head -n 50 dump_xml/$$dict.xml.xml2nvh.nvh ;  done < lexonomy_public_dicts_info.csv.comma > check_result
	rm lexonomy_public_dicts_info.csv.comma

