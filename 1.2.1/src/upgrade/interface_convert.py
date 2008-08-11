#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Converts 1.2 interface/physical interface to 1.2.1 (and back maybe?) """

import sys
import os

def upgrade(dbf, **kw):
    """ To transform from 1.2 to 1.2.1:
            -move mac addr from phys to int
            -move ip addr from varchar to int, nulling where needed
            -create and populate net_id
    """

    from   aquilon.aqdb.db_factory import debug
    import aquilon.aqdb.net.ip_to_int as i2i
    import aquilon.aqdb.hw.interface  as iface

    should_debug = kw.pop('debug', False)
    debug('in interface_update should_debug is %s'%(should_debug))

    #keeps lines < 80 cols
    tbl        = 'interface'
    num_spec   = 'NUMBER(38,0)'
    _MAC       = 'MAC VARCHAR(18)'
    _NET       = 'NETWORK_ID %s'%(num_spec)
    _IP        = 'NEWIP %s'%(num_spec)
    _TYPE      = 'INTERFACE_TYPE VARCHAR(32)'

    #TODO: This doesn't work. We want to build a brand new table with the right,
    #      column order, then select all the existing data into it, then modify
    #     -or- use DBMS.DDL

    #Add the new columns:
    for i in [_MAC, _IP, _NET, _TYPE]:
        stmt  = 'ALTER TABLE %s ADD (%s)'%(tbl,i)
        dbf.safe_execute(stmt, debug=should_debug)

    #depends on network being rebuilt first...should we check on that? How?
        # an upgrade_status table???

    #select each row and update inline:
    for row in dbf.safe_execute(
        """ select A.id, A.ip, B.mac from interface A, physical_interface B
        where A.id = B.interface_id """ ):

        id = row[0]
        ip = row[1]
        mac = row[2]

        if ip == '0.0.0.0':
            ip = 'NULL'
            n_id = 'NULL'
        else:
            network = i2i.get_net_id_from_ip(dbf.session(),ip)
            newip = i2i.dq_to_int(ip)

        # Being lazy with the interface_type field - they're all physical.
        stmt = """update %s set newip = %s,
                                mac   = '%s',
                                interface_type = 'physical',
                                network_id = %s where id = %s """%(
            tbl, newip, mac, network.id , id )

        dbf.safe_execute(stmt,debug=should_debug)

    d1 = 'alter table physical_interface drop column mac'
    dbf.safe_execute(d1, debug=should_debug)

    d2 = 'alter table interface drop column interface_type_id'
    dbf.safe_execute(d2, debug=should_debug)

    r1 = 'alter table interface rename column ip to oldip'
    #rename newip -> ip,
    dbf.safe_execute(r1, debug=should_debug)

    r2 = 'alter table interface rename column newip to ip'
    #we'll hold onto oldip for a few minutes, just in case.
    dbf.safe_execute(r2, debug=should_debug)

    #set ip non null

    nn = """
    alter table %s
        add constraint iface_ip_nn
        check (('ip' is not null))"""%(tbl)

    dbf.safe_execute(nn, debug=should_debug)

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR,
                                                     '..', 'lib', 'python2.5')))
    import aquilon.aqdb.depends

    if '--debug' in sys.argv or '-d' in sys.argv:
        upgrade(debug=True)
    elif '--verbose' in sys.argv or '-v' in sys.argv:
        upgrade(verbose=True)
    else:
        upgrade()
