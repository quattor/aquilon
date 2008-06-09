#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon

from depends import *
from debug import *
from admin import *
from db_factory import db_factory
from admin import constraints

import table_maker
import update_dns_domain
import update_user_princ

import migrate.changeset


dbf = db_factory()
print dbf.dsn
Base.metadata.bind = dbf.engine

### STEP 1
# Full export == safety net
exp = 'exp %s/%s@%s FILE=EXPORT/%s.dmp OWNER=%s DIRECT=n'%(dbf.schema,
                                dbf.schema,dbf.server, dbf.schema, dbf.schema)
print 'running %s'%(exp)
os.system(exp)

### STEP 2: DROP THE STUFF WE DON'T NEED, other arbitrary sql here.

# Drop table ip_addr, network table
d_ip     = 'DROP TABLE IP_ADDR CASCADE CONSTRAINTS'
d_iseq   = 'DROP SEQUENCE IP_ADDR_ID_SEQ'
d_net    = 'DROP TABLE NETWORK CASCADE CONSTRAINTS'
d_nseq   = 'DROP SEQUENCE NETWORK_ID_SEQ'
d_svc_i  = 'DROP TABLE SERVICE_INSTANCE CASCADE CONSTRAINTS'
d_svc_sq = 'DROP SEQUENCE SERVICE_INSTANCE_ID_SEQ'
r_cgf_id = 'ALTER INDEX IX_CFG_PATH_RELATIVE_PATH RENAME TO CFG_PATH_RP_IDX'

drops = [d_ip, d_iseq, d_net, d_nseq, d_svc_i, d_svc_sq]

for d in drops:
    debug(d)
    dbf.safe_execute(d)

# STEP 3: make the new stuff
table_maker.upgrade()



#STEP 4: rename constraints, ignore errors
constraints.rename_non_null_check_constraints(dbf)

#Step 5:More sensitive stuff: table surgery

#DNS DOMAIN:
upd_dns_domain.upgrade()

#USER_PRINCIPAL:
upd_user_princ.upgrade()


#STEP 6: populate/repopulate tables (some 'new' tables were in the old schema)
    #(a)rebuild network table
#process = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)

    #(b)run the add_data script
execfile('add_data.py')

print "Don't forget to cd aqdb dir  and run network.py"
