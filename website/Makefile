bundle.js: $(wildcard riot/*.riot)
	[ -d node_modules ] || npm install
	npm run build
bundle.min.js: bundle.js
	npm run minify
watch:
	npm run watch
install:
	npm install
