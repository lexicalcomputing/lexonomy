all: clean test_create test_import test_clean_nvh test_configs test_projects

test_import.nvh:
	@for i in example_nvh/test_*.nvh; do (cat $$i; echo) >> $@; done

test_import.xml:
	@echo "<DICTIONARY>" > $@
	@for i in example_xml/*.xml; do (cat $$i; echo) >> $@; done
	@echo "</DICTIONARY>" >> $@

# ============================================
# TESTS
# ============================================
test_create:
	./create_dict_test.py

test_import: test_import.xml test_import.nvh
	./import_test.py

test_advance_search:
	./import_test.py TestImportNVH.test_1
	./advance_search_test.py
	./import_test.py TestImportNVH.test_4

test_clean_nvh:
	./clean_nvh_test.py

test_configs:
	./configs_test.py

test_projects:
	./project_test.py

clean:
	rm -rf test_import.nvh test_import.xml