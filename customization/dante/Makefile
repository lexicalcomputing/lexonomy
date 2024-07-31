#Makefile to find and replace title and description in index.html

INDEX_HTML = $(DEPLOYDIR)/website/index.html
TITLE = Dante dictionary - a lexical database for English
DESCRIPTION = A professionally curated English dictionary with API. Contains over 42,000 headwords, 23,000 multiword expressions, and over 27,000 idioms and phrases. Published under the CC-BY licence.

update:
	sed -i 's|<title>.*</title>|<title>$(TITLE)</title>|g' $(INDEX_HTML)
	sed -i 's|<meta name="description" content=".*"/>|<meta name="description" content="$(DESCRIPTION)"/>|g' $(INDEX_HTML)
	@echo "Dante customization finshed, index.html updated"
