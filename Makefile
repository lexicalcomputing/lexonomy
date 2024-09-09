DIST_VERSION=$(shell git describe --tags --always)
INSTALLDIR=dist
SOURCE_RIOT=$(wildcard website/riot/)
SOURCE_JS=website/app.js website/app.static.js website/app.css.js $(SOURCE_RIOT)
INSTALL_JS=bundle.js bundle.css bundle.static.js
SOURCE_PY=lexonomy.py ops.py media.py nvh.py advance_search.py project_gen_next_batch.py import2dict.py project_import_batch.py log_subprocess.py project.py refresh_project_state.py migrate_config.py dmlex2schema.py
SOURCE_CONF=siteconfig.json.template package.json rollup.config.js config.js.template lexonomy.sqlite.schema crossref.sqlite.schema
SOURCE_WEBDIRS=adminscripts css dictTemplates docs furniture img js libs workflows
SOURCE_WEBSITE=$(SOURCE_JS) $(addprefix website/, $(SOURCE_PY) $(SOURCE_CONF) $(SOURCE_WEBDIRS)) website/site.webmanifest website/index.html
INSTALL_WEBSITE=$(addprefix website/, $(INSTALL_JS) $(SOURCE_PY) $(SOURCE_CONF) $(SOURCE_WEBDIRS)) website/site.webmanifest website/index.html
SOURCE_DOCS=AUTHORS INSTALL.md LICENSE README.md Makefile

build: website/bundle.js website/version.txt

website/bundle.js: $(SOURCE_RIOT)
	make -C website

install: $(INSTALL_WEBSITE) $(SOURCE_DOCS) customization
	mkdir -p $(DESTDIR)$(INSTALLDIR)
	cp -rp --parents $^ $(DESTDIR)$(INSTALLDIR)/

deploy:
	mkdir -p $(DEPLOYDIR)/data
	cp website $(DEPLOYDIR)/

	# If new instance create siteconfig.json and config.js
	@if [ ! -f "$(DEPLOYDIR)/website/siteconfig.json" ]; then\
		cat website/siteconfig.json.template | sed "s#%{path}#$(DEPLOYDIR)/website#g" > $(DEPLOYDIR)/website/siteconfig.json; \
		cp website/config.js.template $(DEPLOYDIR)/website/config.js; \
	fi

	@# If CUSTOMIZATION is defined, remove previously deployed website/customization folder and deploy selected customization or all customizations.
	@# - Browse all folders in /customization
	@# - Extract subfolder from path $(folder) and remove trailing slash.
	@# - If folder matches CUSTOMIZATION or CUSTOMIZATION is *, copy files from /customization/$(folder) to $(DEPLOYDIR)/website/customizartion/
	@# - If customization folder contains Makefile, run it.
	@if [ -n "$(CUSTOMIZATION)" ]; then \
		rm -rf $(DEPLOYDIR)/website/customization; \
		$(foreach folder,$(wildcard customization/*/),\
			folder_name=$$(basename $$(echo $(folder) | sed 's:/*$$::')); \
			if [ "$(CUSTOMIZATION)" = "$$folder_name" ] || [ "$(CUSTOMIZATION)" = "*" ]; then \
				echo "Applying customization from $(folder)"; \
				mkdir -p $(DEPLOYDIR)/website/$(folder); \
				cp -R $(folder) $(DEPLOYDIR)/website/customization; \
				if [ -f "$(folder)Makefile" ]; then \
					make -C $(folder) update DEPLOYDIR=$(DEPLOYDIR); \
				fi; \
			fi; \
		)\
	fi

	# Init or update DB
	$(DEPLOYDIR)/website/adminscripts/init_or_update.py
	chmod -R g+rwX $(DEPLOYDIR)/data

website/version.txt:
	git describe --always > $@

dist-gzip: $(SOURCE_WEBSITE) $(SOURCE_DOCS) customization Makefile website/Makefile website/version.txt
	tar czvf lexonomy-$(DIST_VERSION).tar.gz --transform 's,^,lexonomy-$(DIST_VERSION)/,' $^
