#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" The module governing tables and objects that represent IP networks in
    Aquilon."""
from datetime import datetime
import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(DIR, '..'))
import depends

from db_factory import Base
from column_types.aqstr import AqStr
from column_types.IPV4  import IPV4
import ipcalc
from loc.location import Location, location
from loc.building import Building, building
from utils import dsdb

from sqlalchemy import (Column, Table, Integer, Sequence, String, Index,
                        CheckConstraint, UniqueConstraint, DateTime,
                        ForeignKey, insert, select )

from sqlalchemy.orm import relation, deferred, synonym

""" Network Type can be one of four values which have been carried over as
    legacy from the network table in DSDB:
        *   management: no networks have it(@ 3/27/08), it's probably useless

        *   transit: for the phyical interfaces of zebra nodes

        *   vip:     for the zebra addresses themselves

        *   unknown: for network rows in DSDB with NULL values for 'type'

        *   tor_net: tor switches are managed in band, which means that
                     if you know the ip/netmask of the switch, you know the
                     network which it provides for.
"""

#TODO: enum type for network_type, cidr
class Network(Base):
    """
    Represents subnets in aqdb.

    Network Type can be one of four values which have been carried over as
    legacy from the network table in DSDB:
        *   management: no networks have it(@ 3/27/08), it's probably useless
        *   transit: for the phyical interfaces of zebra nodes
        *   vip:     for the zebra addresses themselves
        *   unknown: for network rows in DSDB with NULL values for 'type'

        *   tor: tor switches are managed in band, which means that if you know
                 the ip/netmask of the switch, you know the layer 2 network
                 which it provides access to.
"""

    __tablename__ = 'network'

    id            = Column(Integer,
                           Sequence('network_id_seq'), primary_key = True)

    location_id   = Column('location_id', Integer, ForeignKey('location.id'),
                           nullable=False)

    network_type  = Column(AqStr(32), nullable = False, default = 'unknown')
    cidr          = Column(Integer, nullable = False)
    name          = Column(AqStr(255), nullable = False) #TODO: default to ip
    ip            = Column(String(15), nullable = False)
    side          = Column(AqStr(4), nullable = True, default = 'a')
    dsdb_id       = Column(Integer, nullable = False)

    creation_date = deferred(Column(DateTime, default=datetime.now))
    comments      = deferred(Column(String(255), nullable = True))

    location      = relation(Location, backref = 'networks')

    def _ipcalc(self):
        return ipcalc.Network('%s/%s'%(self.ip,self.cidr))
    ipcalc = property(_ipcalc)

    def _broadcast(self):
        return str(self.ipcalc.broadcast())
    broadcast = property(_broadcast)
    #TODO: netmask property from ipcalc
    #TODO: custom str and repr

network = Network.__table__
network.primary_key.name = 'network_pk'

network.append_constraint(
    UniqueConstraint('dsdb_id', name = 'network_dsdb_id_uk'))

network.append_constraint(
    UniqueConstraint('ip', name = 'net_ip_uk'))

Index('net_loc_id_idx', network.c.location_id)
#TODO: snarf comments  and xx,xw sysloc nets from DSDB (asynchronously?)

def populate(*args, **kw):
    from db_factory import db_factory, Base
    from utils import dsdb

    import logging #do we *need* logger?
        #TODO: when we have an error table, insert a row there, as well as
        #    generating an exception that can be acted upon in dsdb.

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    network.create(checkfirst = True)

    b_cache={}
    sel=select( [location.c.name, building.c.id],
        location.c.id == building.c.id )

    for row in dbf.engine.execute(sel).fetchall():
        b_cache[row[0]]=row[1]

    count=0
    #TODO: forget campus, bucket. make this whole thing an insert ?
    for (name, ip, cidr, type, bldg_name, side, dsdb_id) in dsdb.dump_network():

        kw = {}
        try:
            kw['location_id'] = b_cache[bldg_name]
        except KeyError:
            #TODO: pull the new building in from dsdb somehow
            #TODO: generate an exception about the row if it's got unexpected
            #   null data in it, it means that dsdb has bad data.
            logging.error("Can't find building '%s'\n%s"%(bldg_name, row))
            continue
            # an alternative...
            #sys.stderr.write("Can't find building '%s' for row %s\n"%(
            #    bldg_name,row))

        kw['name']       = name
        kw['ip']         = ip
        kw['cidr']       = cidr
        if type:
            kw['network_type']   = type
        if side:
            kw['side']   = side
        kw['dsdb_id']    = dsdb_id

        c=Network(**kw)
        s.add(c)
        count += 1
        if count % 1000 == 0:
            s.commit()
            s.flush()

    print 'commited %s rows'%(count)
    s.commit()
