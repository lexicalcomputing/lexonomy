all: clean test_import.nvh test_import.xml test_import test_advance_search test_clean_nvh

test_import.nvh:
	for i in example_nvh/test_*.nvh; do (cat $$i; echo) >> $@; done

test_import.xml:
	echo "<DICTIONARY>" > $@
	for i in example_xml/*.xml; do (cat $$i; echo) >> $@; done
	echo "</DICTIONARY>" >> $@

test_import: test_import.xml test_import.nvh
	./import_test.py

test_advance_search: ../../data/dicts/test_import_nvh.sqlite
	./advance_search_test.py

test_clean_nvh:
	./clean_nvh_test.py

clean:
	rm -rf test_import.nvh test_import.xml
	rm -rf test_import.xml.xml2nvh.nvh test_import.*.log test_import.*.schema test_import.*.cleaned
	rm -rf ../../data/dicts/{test_import_xml.sqlite,test_import_nvh.sqlite,test_import_dante.sqlite}
	rm -rf dante.xml.log dante.xml.cleaned dante.xml.xml2nvh.nvh dante.xml.schema