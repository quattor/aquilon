#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" intended to make the new tables during migration """

from depends import *
import migrate.changeset

import schema
import db_factory

###############################REMOVE WHEN STRUNG INTO SINGLE UPGRADE SCRIPT
dbf = db_factory.db_factory()
print dbf.dsn
Base.metadata.bind = dbf.engine
m = Base.metadata
###############

#or meta is already fully reflected???
dns_domain = Table('dns_domain',m,autoload=True)
col = dns_domain.c.creation_date

old_idx_drop = 'DROP INDEX IX_DNS_DOMAIN_NAME'
new_idx_drop = 'DROP INDEX DNS_DOMAIN_UK'

old_idx_cr = 'CREATE UNIQUE INDEX IX_DNS_DOMAIN_NAME ON DNS_DOMAIN(NAME)'
new_idx_cr = 'CREATE UNIQUE INDEX DNS_DOMAIN_UK ON DNS_DOMAIN(NAME)'

def upgrade():
    ## ADD NON NULL CONSTRAINT
    assert col is dns_domain.c.creation_date
    try:
        col.alter(nullable=False)
    except DatabaseError, e:
        print e

    ##ADD UNIQUE index
    try:
        dbf.safe_execute(old_idx_drop)
    except DatabaseError,e:
        print e
        sys.exit(9)

    try:
        idx = Index('dns_domain_uk',dns_domain.c.name, unique = True)
        idx.create()
    except DatabaseError, e:
        print e

    ##UPDATE MS.COM
    print 'before update ms.com'
    print dbf.engine.execute(select([dns_domain])).fetchall()

    dbf.engine.execute(dns_domain.update(dns_domain.c.name=='ms.com'),
                       name = '.ms.com')

    print 'after update ms.com'
    print dbf.engine.execute(select([dns_domain])).fetchall()


def downgrade():
    ##DROP NON NULL
    assert col is dns_domain.c.creation_date
    try:
        col.alter(nullable=True)
    except DatabaseError, e:
        print e

    ##REMOVE UNIQUE INDEX
    dbf.safe_execute(new_idx_drop)
    try:
        old_idx = Index('IX_DNS_DOMAIN_NAME',dns_domain.c.name)
        old_idx.create()
    except DatabaseError, e:
        print e
        sys.exit(9)

    ##REVERT MS.COM
    print 'before downgrade .ms.com'
    print dbf.engine.execute(select([dns_domain])).fetchall()

    dbf.engine.execute(dns_domain.update(dns_domain.c.name=='.ms.com'),
                       name = 'ms.com')

    print 'after downgrade .ms.com'
    print dbf.engine.execute(select([dns_domain])).fetchall()

if __name__ == '__main__':
    upgrade()
    downgrade()
