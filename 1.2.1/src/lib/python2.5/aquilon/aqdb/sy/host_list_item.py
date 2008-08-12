#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Fill in later"""


from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.orderinglist import ordering_list

from aquilon.aqdb.db_factory         import Base
from aquilon.aqdb.sy.host            import Host
from aquilon.aqdb.sy.host_list       import HostList


class HostListItem(Base):
    __tablename__ = 'host_list_item'

    host_list_id = Column(Integer, ForeignKey(
        'host_list.id', ondelete = 'CASCADE', name = 'hli_hl_fk'),
                          primary_key = True)

    host_id = Column(Integer, ForeignKey(
        'host.id', ondelete = 'CASCADE', name = 'hli_host_fk'),
                          primary_key = True)

    position = Column(Integer, nullable = False)

    creation_date = deferred(Column(DateTime, default = datetime.now,
                                    nullable = False))
    comments      = deferred(Column(String(255), nullable = True))

    host          = relation(Host, backref = 'hostlist_items')
    hostlist      = relation(HostList, uselist = False, backref = 'hostlist')

    def __str__(self):
        return str(self.host.name)

    def __repr__(self):
        return self.__class__.__name__ + " " + str(self.host.name)

host_list_item = HostListItem.__table__

host_list_item.primary_key.name = 'host_list_item_pk'

#TODO: would we like this mapped in host_list.py instead?
HostList.hosts = relation(HostListItem,
                          collection_class=ordering_list('position'),
                            order_by=[HostListItem.__table__.c.position])

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base
    from sqlalchemy import insert

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    host_list_item.create(checkfirst = True)

#def populate_hli():
#    if empty(host):
#        print "can't populate host_list_items without hosts."
#        return
#    elif empty(host_list):
#        s=Session()
#
#        hl = HostList(name='test-host-list', comments='FAKE')
#
#        s.save(hl)
#        s.commit()
#        assert(hl)
#
#        hosts=s.query(Host).all()
#        print '%s hosts is in hosts'%(len(hosts))
#
#        hli=HostListItem(hostlist=hl,host=hosts[1], position=1, comments='FAKE')
#        s.save(hli)
#        s.commit()
#        assert(hli)
#        print 'created %s with list items: %s'%(hl,hl.hosts)

    if Base.metadata.bind.echo == True:
        Base.metadata.bind.echo == False
