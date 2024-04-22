DIST_VERSION=$(shell git describe --tags --always)
VERSION=$(shell git describe --tags --abbrev=0)
INSTALLDIR=/usr/share/lexonomy
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
	mkdir -p $(DEPLOYDIR)
	mkdir -p $(DEPLOYDIR)/data
	cp -p libSqliteIcu.so $(DEPLOYDIR)/
	cp -a website $(DEPLOYDIR)/

	# If new instance create siteconfig.json and config.js
	if [ ! -f "$(DEPLOYDIR)/website/siteconfig.json" ]; then\
		cat website/siteconfig.json.template | sed "s#%{path}#$(DEPLOYDIR)/website#g" > $(DEPLOYDIR)/website/siteconfig.json; \
		cp website/config.js.template $(DEPLOYDIR)/website/config.js; \
	fi

	# Init or update DB
	$(DEPLOYDIR)/website/adminscripts/init_or_update.py
	chgrp -R apache $(DEPLOYDIR)/data
	chmod -R g+rwX $(DEPLOYDIR)/data

dist-gzip: $(SOURCE_WEBSITE) $(SOURCE_DOCS) Makefile website/Makefile
	tar czvf lexonomy-$(DIST_VERSION).tar.gz --transform 's,^,lexonomy-$(DIST_VERSION)/,' $^

libSqliteIcu.so: release.tar.gz
	rm -rf sqlite-release
	tar xzf $<
	cd sqlite-release/ext/icu; \
	gcc -fPIC -shared icu.c `pkg-config --libs --cflags icu-uc icu-io` -o libSqliteIcu.so
	cp sqlite-release/ext/icu/libSqliteIcu.so .
	rm -rf sqlite-release

release.tar.gz:
	wget https://github.com/sqlite/sqlite/archive/refs/tags/release.tar.gz









#####################################################################
### Configuration below is for Docker and likely outdated (not used)
#####################################################################

# TARGETS for devs:
# - docker-dev: (prepare everything and) run the dev container
# - docker-lint: run the linter
#
# Update CHANGELOG.md
#   $ GITHUB_TOKEN=INSERT_TOKEN_HERE make CHANGELOG.md
#
# Helper TARGETS:
# - docker-setup: prepare the docker-local volume that will store the node_modules
# - docker-install: (mostly) run `npm install`
#

CHANGELOG_TOKEN := $(if $(GITHUB_TOKEN),--token $(GITHUB_TOKEN),$(""))

.PHONY: docker-dev
docker-dev: docker-install
	docker-compose -f docker-compose-dev.yml run --rm --service-ports dev

.PHONY: docker-lint
docker-lint: docker-quick-install
	docker-compose -f docker-compose-dev.yml run --rm dev npm run lint

.PHONY: CHANGELOG.md
CHANGELOG.md:
	echo $(CHANGELOG_TOKEN)
	docker-compose -f docker-compose-dev.yml run --rm changelog --user elexis-eu --project lexonomy $(CHANGELOG_TOKEN)

# prep targets
#
.PHONY: docker-setup
docker-setup:
	docker volume create nodemodules

.PHONY: docker-install docker-quick-install
docker-install: docker-setup
	docker-compose -f docker-compose-dev.yml run --rm dev npm install --unsafe-perm=true
	docker-compose -f docker-compose-dev.yml run --rm dev pip install -r requirements.txt
docker-quick-install: docker-setup
	docker-compose -f docker-compose-dev.yml run --rm dev npm install --unsafe-perm=true --ignore-scripts
	docker-compose -f docker-compose-dev.yml run --rm dev pip install -r requirements-dev.txt

.PHONY: docker-clean
docker-clean:
	-docker volume rm nodemodules
