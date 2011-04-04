DOCBOOK_VERSION = 5.0
DOCBOOK_XSL_VERSION = 1.75.1
LIBXSLT_VERSION = 1.1.26-2.7.8-z1.2a
LIBXML_VERSION = 2.7.7

DOCBOOK = /ms/dist/fsf/PROJ/docbook/$(DOCBOOK_VERSION)
DOCBOOK_XSL = /ms/dist/fsf/PROJ/docbook-xsl-ns/$(DOCBOOK_XSL_VERSION)/common

XSLTPROC = /ms/dist/gnome/PROJ/libxslt/$(LIBXSLT_VERSION)/exec/bin/xsltproc
XSLT_PARAMS = --xinclude --nonet --catalogs

XMLLINT = /ms/dist/gnome/PROJ/libxml/$(LIBXML_VERSION)/exec/bin/xmllint
# For DocBook 5, the normative description is the Relax NG schema
XMLLINT_PARAMS = --xinclude --nonet --catalogs --noout --relaxng $(DOCBOOK)/rng/docbook.rng

# Used by xsltproc & xmllint to convert URIs to file names
SGML_CATALOG_FILES = $(DOCBOOK)/catalog.xml
export SGML_CATALOG_FILES

FORMATS = man html

COMMAND_SOURCES = $(wildcard commands/*.xml)
ALL_SOURCES = $(wildcard *.xml) $(COMMAND_SOURCES)

all: version.txt $(FORMATS)

man: MAN.MANIFEST

MAN.MANIFEST: $(COMMAND_SOURCES) version.txt
	$(XSLTPROC) $(XSLT_PARAMS) style-man.xsl $(COMMAND_SOURCES)

html: HTML.MANIFEST

HTML.MANIFEST: $(ALL_SOURCES) version.txt
	$(XSLTPROC) $(XSLT_PARAMS) style-html.xsl $(ALL_SOURCES)

# Using git internals as a dependency here is a hack, but that's the only
# way to get the correct version number
version.txt: ../.git/HEAD
	# We don't want the -rc suffix to show up in the man pages
	git describe | sed -e 's/-rc[0-9]\+$$//' > $@.tmp
	# Don't force a full rebuild unless the version has changed
	if cmp -s $@ $@.tmp; then rm -f $@.tmp; else mv $@.tmp $@; fi

clean:
	-rm -f *.MANIFEST
	-rm -rf html
	-rm -rf man
	-rm -f version.txt

install-man: man
	for file in `cat MAN.MANIFEST`; do \
		install -m 644 -D "$$file" "$(DESTDIR)/$$file"; \
	done

install-html: html
	for file in `cat HTML.MANIFEST`; do \
		install -m 644 -D "$$file" "$(DESTDIR)/$$file"; \
	done

install: all install-man install-html

# Use "make check" to validate the XML files. Unfortunately the error
# messages can be misleading sometimes...
check:
	$(XMLLINT) $(XMLLINT_PARAMS) $(SOURCES)

.PHONY: all check clean install install-man install-html man html
