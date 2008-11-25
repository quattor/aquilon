""" The module governing tables and objects that represent IP networks in
    Aquilon."""

from aquilon.aqdb.table_types.name_table import make_name_class

DnsDomain = make_name_class('DnsDomain','dns_domain')
dns_domain = DnsDomain.__table__

table = dns_domain

def populate(sess, *args, **kw):

    if len(sess.query(DnsDomain).all()) < 1:

        ms   = DnsDomain(name = 'ms.com', comments = 'root dns domain')
        onyp = DnsDomain(name = 'one-nyp.ms.com', comments = '1 NYP test domain')
        devin1 = DnsDomain(name = 'devin1.ms.com',
                comments='43881 Devin Shafron Drive domain')
        theha = DnsDomain(name='the-ha.ms.com', comments='HA domain')

        for i in (ms, onyp, devin1, theha):
            sess.add(i)

    sess.commit()




# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
