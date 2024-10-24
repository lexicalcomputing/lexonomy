# Available scripts:
# nvh.py [get|put]
# project_gen_next_batch.py
# import_batch.py
# import2dict.py

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
### stage multi-user ####################################################

### stage snesitive ####################################################
# QUERY need to be specified separatly
SENSITIVE_TITLE="Label sensitive words"
SENSITIVE_DESCRIPTION="Distingush sensitive words from standard words. Eg. fuck vs walk"
SENSITIVE_ANNOTATOR_NAME="Sensitivity annotator"
SENSITIVE_QUERY="entry.sense"

sensitive_new_batches: $(SOURCE_DICT)
	$(DIR)/nvh.py get $< $(SENSITIVE_QUERY) | $(GEN_NEXT_BATCH) | parallel "echo {} | $(IMPORT_BATCH)"

sensitive.nvh: $(SOURCE_DICT) $(ACCEPTED_BATCHES)
	cat $(filter-out $<,$^) > $@.patch
	$(DIR)/nvh.py put $< $@.patch > $@
	$(DIR)/import2dict.py $(DICT_DB) $@ $(USER) $(TL_NODE)

### stage images ####################################################
IMAGES_TITLE="Assign image"
IMAGES_DESCRIPTION="Pick the most probable image for provided word"
IMAGES_ANNOTATOR_NAME="Image selector"
IMAGES_QUERY="entry"

images_new_batches: $(SOURCE_DICT)
	$(DIR)/nvh.py get $< $(IMAGES_QUERY) | $(GEN_NEXT_BATCH) | parallel "echo {} | $(IMPORT_BATCH)"

images.nvh: $(SOURCE_DICT) $(ACCEPTED_BATCHES)
	cat $(filter-out $<,$^) > $@.patch 
	$(DIR)/nvh.py put $< $@.patch > $@
	$(DIR)/import2dict.py $(DICT_DB) $@ $(USER) $(TL_NODE)

### stage images ####################################################
SENS_EXAMPLES_TITLE="Assign sense examples"
SENS_EXAMPLES_DESCRIPTION="Create example for sense"
SENS_EXAMPLES_ANNOTATOR_NAME="Sense examples"
SENS_EXAMPLES_QUERY="entry.sense"

sens_examples_new_batches: sensitive.nvh
	$(DIR)/nvh.py get $< $(SENSEXAMPLES_QUERY) | $(GEN_NEXT_BATCH) | parallel "echo {} | $(IMPORT_BATCH)"

sens_examples.nvh: sensitive.nvh $(ACCEPTED_BATCHES)
	cat $(filter-out $<,$^) > $@.patch 
	$(DIR)/nvh.py put $< $@.patch > $@
	$(DIR)/import2dict.py $(DICT_DB) $@ $(USER) $(TL_NODE)

### stage merge ####################################################
FINAL_TITLE="Marge annotations"
FINAL_DESCRIPTION="Combine all annotations from previous stages into final dictionary"

final.nvh: $(SOURCE_DICT) sensitive.nvh images.nvh
	$(DIR)/nvh.py put $< sensitive.nvh > $@.patch
	$(DIR)/nvh.py put $@.patch images.nvh > $@
	$(DIR)/import2dict.py $(DICT_DB) $@ $(USER) $(TL_NODE)
