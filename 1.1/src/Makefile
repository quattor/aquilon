PYTHON = //ms/dist/python/PROJ/core/2.5/bin/python2.5
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
  $(error Unable to parse meta/proj/rel from cwd '$(PWD)')
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
ETC_FILES := $(shell find etc -type f)
PYC_FILES := $(shell find lib -name '*.py' | sed -e 's,\.py,\.pyc,')

FILES = $(BIN_FILES) $(LIB_FILES) $(MAN_FILES) $(ETC_FILES) $(PYC_FILES)
INSTALLFILES = $(addprefix $(COMMON),$(FILES))

$(COMMON)bin/%: bin/%
	@mkdir -p `dirname $@`
	install -m $(PERMS) $< $@

$(COMMON)%.pyc: $(COMMON)%.py
	@echo "compiling $@"
	@rm -f $@
	@$(PYTHON) -mpy_compile $<

$(COMMON)lib/%: lib/%
	@mkdir -p `dirname $@`
	install -m $(LIB_PERMS) $< $@

$(COMMON)etc/%: etc/%
	@mkdir -p `dirname $@`
	install -m $(LIB_PERMS) $< $@

$(COMMON)etc/rc.d/init.d/aqd: etc/rc.d/init.d/aqd
	@mkdir -p `dirname $@`
	install -m 055 $< $@

.PHONY: install
install: $(INSTALLFILES)

.PHONY: default
default:
	@echo "Use 'gmake install' to install ${META}/${PROJ}/${REL}"

.PHONY: update
update:
	p4 sync ...

.PHONY: prodlink
prodlink:
	vms turnover releaselink ${META} ${PROJ} ${REL} prod

.PHONY: betalink
betalink:
	vms turnover releaselink ${META} ${PROJ} ${REL} beta

.PHONY: to
to:
	vms turnover release ${META} ${PROJ} ${REL}

.PHONY: distqa
distqa: to
	vms dist ${META} ${PROJ} ${REL} -- -cells ${QCELLS} ${QACOMMENT}

.PHONY: distworld
distworld: to
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

.PHONY: create
create:
	vms create release ${META} ${PROJ} ${REL} -- -noinstall -nobuildvolume
	vms create install ${META} ${PROJ} ${REL} common

.PHONY: upd-dist
upd-dist: unlock update install distworld 
