VERSION=$(shell git describe --tags --always)
INSTALLDIR=/opt/lexonomy
SOURCE_RIOT=$(wildcard website/riot/*.riot)
SOURCE_JS=website/app.js $(SOURCE_RIOT)
INSTALL_JS=app.js bundle.js
SOURCE_PY=lexonomy.py ops.py bottle.py media.py
SOURCE_CONF=siteconfig.json.template package.json rollup.config.js
SOURCE_WEBDIRS=adminscripts css dictTemplates docs furniture img js libs
SOURCE_WEBSITE=$(SOURCE_JS) $(addprefix website/, $(SOURCE_PY) $(SOURCE_CONF) $(SOURCE_WEBDIRS))
INSTALL_WEBSITE=$(addprefix website/, $(INSTALL_JS) $(SOURCE_PY) $(SOURCE_CONF) $(SOURCE_WEBDIRS))
SOURCE_DOCS=AUTHORS INSTALL.md LICENSE README.md data/README.md data/dicts/README.md data/uploads/README.md

build: website/bundle.js
website/bundle.js: $(SOURCE_RIOT)
	make -C website
install: $(INSTALL_WEBSITE) $(SOURCE_DOCS)
	mkdir -p $(DESTDIR)$(INSTALLDIR)
	cp -rp --parents $^ $(DESTDIR)$(INSTALLDIR)/
	mv $(DESTDIR)$(INSTALLDIR)/website/siteconfig.json.template $(DESTDIR)$(INSTALLDIR)/website/siteconfig.json
dist-gzip: $(SOURCE_WEBSITE) $(SOURCE_DOCS) Makefile website/Makefile
	tar czvf lexonomy-$(VERSION).tar.gz --transform 's,^,lexonomy-$(VERSION)/,' $^










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
