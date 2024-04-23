DIST_VERSION=$(shell git describe --tags --always)
INSTALLDIR=dist
SOURCE_RIOT=$(wildcard website/riot/)
SOURCE_JS=website/app.js website/app.static.js website/app.css.js $(SOURCE_RIOT)
INSTALL_JS=bundle.js bundle.css bundle.static.js
SOURCE_PY=lexonomy.py ops.py media.py nvh.py advance_search.py import.py
SOURCE_CONF=siteconfig.json.template package.json rollup.config.js config.js.template lexonomy.sqlite.schema crossref.sqlite.schema
SOURCE_WEBDIRS=adminscripts css dictTemplates docs furniture img js libs workflows
SOURCE_WEBSITE=$(SOURCE_JS) $(addprefix website/, $(SOURCE_PY) $(SOURCE_CONF) $(SOURCE_WEBDIRS)) website/index.html
INSTALL_WEBSITE=$(addprefix website/, $(INSTALL_JS) $(SOURCE_PY) $(SOURCE_CONF) $(SOURCE_WEBDIRS)) website/index.html
SOURCE_DOCS=AUTHORS INSTALL.md LICENSE README.md Makefile

build: website/bundle.js

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

	# Init or update DB
	$(DEPLOYDIR)/website/adminscripts/init_or_update.py
	chgrp -R `id -g apache` $(DEPLOYDIR)/data
	chmod -R g+rwX $(DEPLOYDIR)/data

dist-gzip: $(SOURCE_WEBSITE) $(SOURCE_DOCS) Makefile website/Makefile
	tar czvf lexonomy-$(DIST_VERSION).tar.gz --transform 's,^,lexonomy-$(DIST_VERSION)/,' $^
