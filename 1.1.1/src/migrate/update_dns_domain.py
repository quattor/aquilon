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


if __name__ == '__main__':
    dbf = db_factory.db_factory()
    print dbf.dsn
    Base.metadata.bind = dbf.engine

    m = Base.metadata

    dns_domain = Table('dns_domain',m,autoload=True)

    #print 'Before alter columns: %s'%(dns_domain.__dict__)

    col = dns_domain.c.creation_date
    assert col is dns_domain.c.creation_date

    col.alter(nullable=False)
    print 'After alter column: %s'%(dns_domain.__dict__)

    col.alter(nullable=True)
    #print 'After re-alter column: %s'%(dns_domain.__dict__)



#def make_null(tbl,col):
#    col.alter(nullable=True)
    #d_col = schema.get_date_col()
    #c_col = schema.get_comment_col()
    #
    #c_col.create(dns_domain)
    #d_col.create(dns_domain)
    #
    #print 'After add columns: %s'%(dns_domain.columns)
    #
    #c_col.drop(dns_domain)
    #d_col.drop(dns_domain)
    #
    #print 'After drop columns: %s'%(dns_domain.columns)

    #from IPython.Shell import IPShellEmbed
    #ipshell = IPShellEmbed()
    #ipshell()
