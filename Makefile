SHELL  = /bin/ksh
COMMON = ../install/common/
QACOMMENT = -comment cmrs=qa
QCELLS = q.ny,q.ln,q.hk,q.tk
TCM_COMMENT = "-comment tcm FILL IT IN NOW"

MPR    := $(shell echo $(PWD) | awk -F/ '{print $$(NF-3), $$(NF-2), $$(NF-1)}')
META   = $(word 1,$(MPR))
PROJ   = $(word 2,$(MPR))
REL    = $(word 3,$(MPR))

ifneq (aquilon,$(META))
	META = aquilon
	PROJ = aqd
	REL := $(shell git describe | awk -F- '{print $$1}')
endif

# determine if we're in /ms/dev or our shadow
# keep them owner writeable in shadow install
PERMS = 755
LIB_PERMS = 644

IN_AFS = $(findstring /ms/dev/aquilon/aqd, $(PWD))
ifneq (,$(IN_AFS))
        COMMON = /ms/dev/aquilon/aqd/$(REL)/install/common/
        PERMS = 555
        LIB_PERMS = 444
endif

#try make print-LIB_DIRS for an example
#IF YOU WANT THE FILE DEFINED FROM, ADD (from $(origin $*))
print-%: ; @$(error $* is $($*) ($(value $*)))


# Here, we make some very easy to parse, and perhaps not very subtle,
# The goal is to be readable by someone who doesn't know make very well,
# to make it maintainable, not to impress you with how well I know the tool

BIN_FILES := $(shell find bin -type f)
LIB_FILES := $(shell find lib -type f)
ETC_FILES := $(shell find etc -type f | grep -v templates)
PYC_FILES := $(shell find lib -name '*.py' | sed -e 's,\.py,\.pyc,')

FILES = $(BIN_FILES) $(LIB_FILES) $(MAN_FILES) $(ETC_FILES) $(PYC_FILES)
INSTALLFILES = $(addprefix $(COMMON),$(FILES))

$(COMMON)bin/%: bin/%
	@mkdir -p `dirname $@`
	install -m $(PERMS) $< $@

$(COMMON)%.pyc: $(COMMON)%.py
	@echo "compiling $@"
	@rm -f $@
	./compile_for_dist.py $<

$(COMMON)lib/%: lib/%
	@mkdir -p `dirname $@`
	install -m $(LIB_PERMS) $< $@

$(COMMON)etc/%: etc/%
	@mkdir -p `dirname $@`
	install -m $(LIB_PERMS) $< $@

$(COMMON)etc/rc.d/init.d/aqd: etc/rc.d/init.d/aqd
	@mkdir -p `dirname $@`
	install -m 0555 $< $@

# Running twistd after all the files have been installed generates a
# dropin.cache file that would otherwise be missing (and that missing
# file causes the server to complain loudly on startup).
# The file will only be generated as needed.  The remove_stale script
# skips dropin.cache.
#
# For gen_completion.py, there's no point in doing something make-like
# and sophisticated for this, since remove_stale is dumb and will always
# remove the generated files anyway.
.PHONY: install
install: remove_stale $(INSTALLFILES)
	$(COMMON)bin/twistd --help >/dev/null
	./gen_completion.py --outputdir="$(COMMON)etc" --templatedir="./etc/templates" --all

.PHONY: remove_stale
remove_stale:
	./remove_stale.py "$(COMMON)"

.PHONY: default
default:
	@echo "Use 'gmake install' to install ${META}/${PROJ}/${REL}"

# The second find needs to ignore the .git directory... just doing a
# find on * is an easy/legit way to do that in this case.
.PHONY: clean
clean:
	find . -name '*.pyc' -exec rm {} \;
	find * -type d -empty -exec rmdir {} \;

.PHONY: prodlink
prodlink:
	vms turnover releaselink ${META} ${PROJ} ${REL} prod

.PHONY: betalink
betalink:
	vms turnover releaselink ${META} ${PROJ} ${REL} beta

.PHONY: to
to:
	vms turnover release ${META} ${PROJ} ${REL}

.PHONY: to_nolock
to_nolock:
	vms turnover release ${META} ${PROJ} ${REL} -- -nolock

.PHONY: distqa
distqa: to_nolock
	vms dist ${META} ${PROJ} ${REL} -- -cells ${QCELLS} ${QACOMMENT}

.PHONY: distworld
distworld: to_nolock
	vms dist ${META} ${PROJ} ${REL} -- -gl ${QACOMMENT}

.PHONY: distfinal
distfinal: to
	vms dist ${META} ${PROJ} ${REL} -- -gl ${QACOMMENT}

.PHONY: unlock
unlock:
	vms unlock release ${META} ${PROJ} ${REL}

.PHONY: freeze
freeze:
	vms freezedist ${META} ${PROJ}

.PHONY: thaw
thaw:
	vms thawdist ${META} ${PROJ}

# Handled by SCM/GNUmakefile
.PHONY: create
create:
	vms create release ${META} ${PROJ} ${REL} -- -nobuildvolume
	vms create install ${META} ${PROJ} ${REL} common

