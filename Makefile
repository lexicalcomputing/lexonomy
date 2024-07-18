DIST_VERSION=$(shell git describe --tags --always)
INSTALLDIR=dist
SOURCE_RIOT=$(wildcard website/riot/)
SOURCE_JS=website/app.js website/app.static.js website/app.css.js $(SOURCE_RIOT)
INSTALL_JS=bundle.js bundle.css bundle.static.js
SOURCE_PY=lexonomy.py ops.py media.py nvh.py advance_search.py gen_next_batch.py import2dict.py import_batch.py log_subprocess.py
SOURCE_CONF=siteconfig.json.template package.json rollup.config.js config.js.template lexonomy.sqlite.schema crossref.sqlite.schema
SOURCE_WEBDIRS=adminscripts css customization dictTemplates docs furniture img js libs workflows
SOURCE_WEBSITE=$(SOURCE_JS) $(addprefix website/, $(SOURCE_PY) $(SOURCE_CONF) $(SOURCE_WEBDIRS)) website/index.html
INSTALL_WEBSITE=$(addprefix website/, $(INSTALL_JS) $(SOURCE_PY) $(SOURCE_CONF) $(SOURCE_WEBDIRS)) website/index.html
SOURCE_DOCS=AUTHORS INSTALL.md LICENSE README.md Makefile

build: website/bundle.js website/version.txt

website/bundle.js: $(SOURCE_RIOT)
	make -C website

install: $(INSTALL_WEBSITE) $(SOURCE_DOCS)
	mkdir -p $(DESTDIR)$(INSTALLDIR)
	cp -rp --parents $^ $(DESTDIR)$(INSTALLDIR)/

deploy:
	mkdir -p $(DEPLOYDIR)/data
	cp -a website $(DEPLOYDIR)/

	# If new instance create siteconfig.json and config.js
	if [ ! -f "$(DEPLOYDIR)/website/siteconfig.json" ]; then\
		cat website/siteconfig.json.template | sed "s#%{path}#$(DEPLOYDIR)/website#g" > $(DEPLOYDIR)/website/siteconfig.json; \
		cp website/config.js.template $(DEPLOYDIR)/website/config.js; \
	fi

	if [ -n "$(CUSTOMIZATION)" ]; then \
		rm -rf $(DEPLOYDIR)/website/customization; \
		if [ "$(CUSTOMIZATION)" = "*" ]; then \
			cp -R customization $(DEPLOYDIR)/website/customization; \
		else \
			if [ -d customization/$(CUSTOMIZATION) ]; then \
				mkdir -p $(DEPLOYDIR)/website/customization/$(CUSTOMIZATION); \
				cp -R customization/$(CUSTOMIZATION) $(DEPLOYDIR)/website/customization/; \
			else \
				echo "Source customization folder not found at customization/$(CUSTOMIZATION)"; \
			fi; \
		fi; \
	fi


	# Init or update DB
	$(DEPLOYDIR)/website/adminscripts/init_or_update.py
	chmod -R g+rwX $(DEPLOYDIR)/data

website/version.txt:
	git describe --always > $@

dist-gzip: $(SOURCE_WEBSITE) $(SOURCE_DOCS) Makefile website/Makefile website/version.txt
	tar czvf lexonomy-$(DIST_VERSION).tar.gz --transform 's,^,lexonomy-$(DIST_VERSION)/,' $^
