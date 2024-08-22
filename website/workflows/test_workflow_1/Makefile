# ============================
# VARIABLES - Include in each workflow
# ============================
ACCEPTED_BATCHES=$(wildcard $(ACCEPTED_BATCHES_FILEMASK))
DIR=%dir%
TL_NODE=entry

TS=\"$$(TZ=UTC date +%Y-%m-%d" "%H:%M:%S.%N)\"
GEN_NEXT_BATCH=$(DIR)/project_gen_next_batch.py $(BATCH_SIZE) $(MAX_BATCHES) $(GENERATED_BATCHES_FILEMASK) $(TL_NODE)
IMPORT_BATCH=$(DIR)/project_import_batch.py $(USER) $(TL_NODE) $(TS)
# ============================

### stage snesitive ####################################################
# QUERY need to be specified separatly
SENSITIVE_QUERY="entry.sense"

sensitive_new_batches: $(SOURCE_DICT)
	$(DIR)/nvh.py get $< $(SENSITIVE_QUERY) | $(GEN_NEXT_BATCH) | parallel "echo {} | $(IMPORT_BATCH)"

sensitive.nvh: $(SOURCE_DICT) $(ACCEPTED_BATCHES)
	cat $(filter-out $<,$^) > $@.patch
	$(DIR)/nvh.py put $< $@.patch > $@
	$(DIR)/import2dict.py $(DICT_DB) $@ $(USER) $(TL_NODE)

### stage images ####################################################
IMAGES_QUERY="entry"

images_new_batches: $(SOURCE_DICT)
	$(DIR)/nvh.py get $< $(IMAGES_QUERY) | $(GEN_NEXT_BATCH) | parallel "echo {} | $(IMPORT_BATCH)"

images.nvh: $(SOURCE_DICT) $(ACCEPTED_BATCHES)
	cat $(filter-out $<,$^) > $@.patch 
	$(DIR)/nvh.py put $< $@.patch > $@
	$(DIR)/import2dict.py $(DICT_DB) $@ $(USER) $(TL_NODE)

### stage images ####################################################
SENS_EXAMPLES_QUERY="entry.sense"

sens_examples_new_batches: sensitive.nvh
	$(DIR)/nvh.py get $< $(SENSEXAMPLES_QUERY) | $(GEN_NEXT_BATCH) | parallel "echo {} | $(IMPORT_BATCH)"

sens_examples.nvh: sensitive.nvh $(ACCEPTED_BATCHES)
	cat $(filter-out $<,$^) > $@.patch 
	$(DIR)/nvh.py put $< $@.patch > $@
	$(DIR)/import2dict.py $(DICT_DB) $@ $(USER) $(TL_NODE)

### stage merge ####################################################
final.nvh: $(SOURCE_DICT) sensitive.nvh images.nvh
	$(DIR)/nvh.py put $< sensitive.nvh > $@.patch
	$(DIR)/nvh.py put $@.patch images.nvh > $@
	$(DIR)/import2dict.py $(DICT_DB) $@ $(USER) $(TL_NODE)
