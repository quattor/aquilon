#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Classes and Tables relating to network interfaces"""


from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Column, Table, Integer, Sequence, String, Index,
                        Boolean, CheckConstraint, UniqueConstraint, DateTime,
                        ForeignKey, PrimaryKeyConstraint, insert, select)
from sqlalchemy.orm import mapper, relation, deferred

from aquilon.aqdb.column_types.aqmac import AqMac
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.column_types.IPV4  import IPV4
from aquilon.aqdb.db_factory         import Base
from aquilon.aqdb.net.network        import Network


class Interface(Base):
    __tablename__ = 'interface'

    id             = Column(Integer,
                            Sequence('interface_id_seq'), primary_key=True)

    interface_type = Column(AqStr(32), nullable = False) #TODO: index
    mac            = Column(AqMac(18), nullable = False)
    ip             = Column(IPV4, nullable = True)
    network_id     = Column(Integer, ForeignKey(Network.__table__.c.id,
                                                name = 'iface_net_id_fk'),
                            nullable = True)

    creation_date  = deferred(Column('creation_date',
                                    DateTime, default = datetime.now,
                                    nullable = False))

    comments       = deferred(Column(
                                'comments',String(255))) #TODO FK to IP table)
    network        = relation(Network, backref = 'interfaces' )

    __mapper_args__ = {'polymorphic_on' : interface_type}

interface = Interface.__table__
interface.primary_key.name = 'interface_pk'

interface.append_constraint(UniqueConstraint('mac', name = 'iface_mac_addr_uk'))
interface.append_constraint(UniqueConstraint('ip',  name = 'iface_ip_addr_uk'))
Index('iface_net_id_idx', interface.c.network_id)

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base
    from sqlalchemy import insert

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    interface.create(checkfirst=True)

    if len(s.query(Interface).all()) < 1:
        #print 'no interfaces yet'
        pass

    if Base.metadata.bind.echo == True:
        Base.metadata.bind.echo == False
