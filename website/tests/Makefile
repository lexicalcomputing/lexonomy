all: clean test_import.nvh test_import.xml test_import test_advance_search

test_import.nvh:
	for i in example_nvh/*.nvh; do (cat $$i; echo) >> $@; done

test_import.xml:
	echo "<DICTIONARY>" > $@
	for i in example_xml/*.xml; do (cat $$i; echo) >> $@; done
	echo "</DICTIONARY>" >> $@

test_import: test_import.xml test_import.nvh
	./import_test.py

test_advance_search: ../../data/dicts/test_import_nvh.sqlite
	./advance_search.py

clean:
	rm -rf test_import.xml.xml2nvh.nvh test_import.*.err test_import.*.pid ../../data/dicts/test_import_xml.sqlite ../../data/dicts/test_import_nvh.sqlite
