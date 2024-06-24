ACCEPTED_BATCHES=$(wildcard $(ACCEPTED_BATCHES_FILEMASK))
DIR=%dir%
TL_NODE=entry

### stage snesitive ####################################################
sensitive_new_batches: $(SOURCE_DICT)
	$(DIR)/nvh.py get $< entry.sense | $(DIR)/gen_next_batch.py $(BATCH_SIZE) $(MAX_BATCHES) $(GENERATED_BATCHES_FILEMASK) $(TL_NODE) | parallel "echo {} | $(DIR)/import_batch.py $(USER) $(TL_NODE)"

sensitive.nvh: $(SOURCE_DICT) $(ACCEPTED_BATCHES)
	cat $(filter-out $<,$^) > $@.patch
	$(DIR)/nvh.py put $< $@.patch > $@
	$(DIR)/import2dict.py $(DICT_DB) $@ $(USER) $(TL_NODE)

### stage images ####################################################
images_new_batches: $(SOURCE_DICT)
	$(DIR)/nvh.py get $< entry | $(DIR)/gen_next_batch.py $(BATCH_SIZE) $(MAX_BATCHES) $(GENERATED_BATCHES_FILEMASK) $(TL_NODE) | parallel "echo {} | $(DIR)/import_batch.py $(USER) $(TL_NODE)"

images.nvh: $(SOURCE_DICT) $(ACCEPTED_BATCHES)
	cat $(filter-out $<,$^) > $@.patch
	$(DIR)/nvh.py put $< $@.patch > $@
	$(DIR)/import2dict.py $(DICT_DB) $@ $(USER) $(TL_NODE)

### stage merge ####################################################
final.nvh: $(SOURCE_DICT) sensitive.nvh images.nvh
	$(DIR)/nvh.py put $< sensitive.nvh > $@.patch
	$(DIR)/nvh.py put $@.patch images.nvh > $@
	$(DIR)/import2dict.py $(DICT_DB) $@ $(USER) $(TL_NODE)
