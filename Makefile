DIST_VERSION=$(shell git describe --tags --always)
INSTALLDIR=dist
SOURCE_RIOT=$(wildcard website/riot/)
SOURCE_JS=website/app.js.template website/app.static.js website/app.styles.scss website/codemirror.js $(SOURCE_RIOT)
INSTALL_JS=bundle.js bundle.css bundle.static.js bundle.codemirror.js
SOURCE_PY=lexonomy.py ops.py media.py nvh.py advance_search.py project_gen_next_batch.py import2dict.py project_import_batch.py log_subprocess.py project.py refresh_project_state.py migrate_config.py dmlex2schema.py nvh_formatting_editor.py
SOURCE_CONF=siteconfig.json.template package.json rollup.config.js rollup.config.codemirror.js config.js.template lexonomy.sqlite.schema crossref.sqlite.schema site.webmanifest
SOURCE_WEBDIRS=adminscripts css dictTemplates docs furniture img js libs workflows
SOURCE_WEBSITE=$(SOURCE_JS) $(addprefix website/, $(SOURCE_PY) $(SOURCE_CONF) $(SOURCE_WEBDIRS)) website/site.webmanifest website/index.html
INSTALL_WEBSITE=$(addprefix website/, $(INSTALL_JS) $(SOURCE_PY) $(SOURCE_CONF) $(SOURCE_WEBDIRS)) website/site.webmanifest website/index.html
SOURCE_DOCS=AUTHORS INSTALL.md LICENSE README.md Makefile

all: website/bundle.js website/version.txt
	./website/adminscripts/init_or_update.py

build: website/bundle.js

website/bundle.js: $(SOURCE_RIOT)
	make -C website

install: $(INSTALL_WEBSITE) $(SOURCE_DOCS)
	mkdir -p $(DESTDIR)$(INSTALLDIR)
	cp -rp --parents $^ $(DESTDIR)$(INSTALLDIR)/

deploy:
	cp -r website $(DEPLOYDIR)/
	$(DEPLOYDIR)/website/adminscripts/init_or_update.py --no-backup

deploy_and_backup:
	cp -r website $(DEPLOYDIR)/
	$(DEPLOYDIR)/website/adminscripts/init_or_update.py

website/version.txt:
	git describe --tags --abbrev=0 | sed "s/beta-//g" > $@

dist-gzip: $(SOURCE_WEBSITE) $(SOURCE_DOCS) Makefile website/Makefile website/version.txt
	tar czvf lexonomy-$(DIST_VERSION).tar.gz --transform 's,^,lexonomy-$(DIST_VERSION)/,' $^
