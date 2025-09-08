# Available scripts:
# nvh.py [get|put]
# project_gen_next_batch.py
# import_batch.py
# import2dict.py

# ============================
# INFO
# ============================
# these variables *._TITLE, *._DESCRIPTION, *._ANNOTATOR_NAME, *._TYPE, *._QUERY are used in lexonomy project info

# ============================
# RESTRICTIONS
# ============================
# .*_TYPE varaible is required for each stage availabel options: merge, gen_batch
# .*_QUERY variable required for stages of type gen_batch
# don't create variables with name *._TITLE, *._DESCRIPTION, *._ANNOTATOR_NAME, *._TYPE, *._QUERY

# ============================
# VARIABLES INICIALIZED FROM SHELL
# ============================
# USER 
# BATCH_SIZE
# MAX_BATCHES
# ACCEPTED_BATCHES_FILEMASK
# GENERATED_BATCHES_FILEMASK

# ============================
# VARIABLES - Include in each workflow (REQUIRED
# ============================
ACCEPTED_BATCHES=$(wildcard $(ACCEPTED_BATCHES_FILEMASK))
DIR=%dir%
TL_NODE=entry

TS=\"$$(TZ=UTC date +%Y-%m-%d" "%H:%M:%S.%N)\"
GEN_NEXT_BATCH=$(DIR)/project_gen_next_batch.py $(BATCH_SIZE) $(MAX_BATCHES) $(GENERATED_BATCHES_FILEMASK) $(TL_NODE)
IMPORT_BATCH=$(DIR)/project_import_batch.py $(USER) $(TL_NODE) $(TS)
# ============================
### stage multi-user ####################################################
# TODO

### stage headwords ####################################################
# QUERY need to be specified separatly
HEADWORDS_TITLE="Label headwords"
HEADWORDS_DESCRIPTION="Distinguish dictionary words from non-words/incorrect words"
HEADWORDS_ANNOTATOR_NAME="Headword annotator"
HEADWORDS_TYPE="gen_batch"
HEADWORDS_QUERY="entry"

headwords_new_batches: $(SOURCE_DICT)
	$(DIR)/nvh.py get $< $(SENSITIVE_QUERY) | grep -v "__lexonomy__complete" | $(GEN_NEXT_BATCH) | parallel "echo {} | $(IMPORT_BATCH)"

headwords.nvh: $(SOURCE_DICT)
	cat $(ACCEPTED_BATCHES) > $@.patch
	$(DIR)/nvh.py put $< $@.patch > $@.merged
	$(DIR)/nvh.py get $@.merged entry.headwords__flag=ok > $@
	$(DIR)/import2dict.py $(DICT_DB) $@ $(USER) $(TL_NODE)

### stage sensitivity ####################################################
SENSITIVE_TITLE="Label sensitive words"
SENSITIVE_DESCRIPTION="Distingush sensitive words from standard words. Eg. fuck vs walk"
SENSITIVE_ANNOTATOR_NAME="Sensitivity annotator"
SENSITIVE_TYPE="gen_batch"
SENSITIVE_QUERY="entry"

sensitive_new_batches: headwords.nvh
	$(DIR)/nvh.py get $< $(SENSITIVE_QUERY) | grep -v "__lexonomy__complete" | $(GEN_NEXT_BATCH) | parallel "echo {} | $(IMPORT_BATCH)"

sensitive.nvh: headwords.nvh
	cat $(ACCEPTED_BATCHES) > $@.patch
	$(DIR)/nvh.py put $< $@.patch > $@.merged
	$(DIR)/nvh.py get $@.merged entry.sensitive__flag > $@
	$(DIR)/import2dict.py $(DICT_DB) $@ $(USER) $(TL_NODE)

### stage examples ####################################################
EXAMPLES_TITLE="Select examples"
EXAMPLES_DESCRIPTION="Select eligible examples for headword"
EXAMPLES_ANNOTATOR_NAME="Exmaples annotator"
EXAMPLES_TYPE="gen_batch"
EXAMPLES_QUERY="entry"

examples_new_batches: headwords.nvh
	$(DIR)/nvh.py get $< $(SENSITIVE_QUERY) | grep -v "__lexonomy__complete" | $(GEN_NEXT_BATCH) | parallel "echo {} | $(IMPORT_BATCH)"

examples.nvh: headwords.nvh
	cat $(ACCEPTED_BATCHES) > $@.patch
	$(DIR)/nvh.py put $< $@.patch > $@.merged
	$(DIR)/nvh.py get $@.merged entry.example.flag='ok' entry.pos,entry.postitle,entry.lemma,entry.headwords__flag,entry.sensitive__flag,entry.example > $@
	$(DIR)/import2dict.py $(DICT_DB) $@ $(USER) $(TL_NODE)

### stage merge ####################################################
FINAL_TITLE="Marge all annotations"
FINAL_DESCRIPTION="Combine all annotations from previous stages (headwords, sensitive, examples) into final dictionary"
FINAL_TYPE="merge"

final.nvh: headwords.nvh sensitive.nvh examples.nvh
	$(DIR)/nvh.py put headwords.nvh sensitive.nvh > $@.sensitive.patch
	$(DIR)/nvh.py put $@.sensitive.patch examples.nvh > $@.examples.patch
	$(DIR)/nvh.py get $@.examples.patch entry.example.flag='ok' entry.pos,entry.postitle,entry.lemma,entry.headwords__flag,entry.sensitive__flag,entry.example > $@
	$(DIR)/import2dict.py $(DICT_DB) $@ $(USER) $(TL_NODE)
