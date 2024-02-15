test_import.nvh:
	for i in example_nvh/*.nvh; do (cat $$i; echo) >> $@; done

test_db/test_import.sqlite: test_import.nvh
	rm -rf test_db
	./import.py -i $^

test_advance_search: test_db/test_import.sqlite
	./advance_search.py

clean:
	rm -rf test.sqlite