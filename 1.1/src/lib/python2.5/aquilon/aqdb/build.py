#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Left in its own module as it depends on many of the others to exist
    first to avoid circular dependencies """
import datetime

import sys
sys.path.append('../..')

from db import *
from service import Host
from configuration import CfgPath
from aquilon.aqdb.utils.schemahelpers import *

from sqlalchemy import Column, Integer, Sequence, String, ForeignKey
from sqlalchemy.orm import mapper, relation, deferred

host     = Table('host', meta, autoload=True)
cfg_path = Table('cfg_path', meta, autoload=True)


build = Table('build', meta,
    Column('id', Integer, primary_key=True),
    Column('host_id', Integer,
           ForeignKey('host.id'), unique=True, nullable=False, index=True),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
build.create(checkfirst=True)

class Build(aqdbBase):
    """ Identifies the build process of a given Host.
        Parent of 'build_element' """
    def __init__(self,host):
        if isinstance(host,Host):
            self.host=host
        else:
            msg = 'Build object requires a Host object for its constructor'
            raise ArgumentError()
    def __repr__(self):
        return 'Build Information for %s'%(self.host.name)

mapper(Build,build,properties={
    'creation_date' : deferred(build.c.creation_date),
    'comments': deferred(build.c.comments)
})

build_element = Table('build_element', meta,
    Column('id',Integer, primary_key=True),
    Column('build_id', Integer,
           ForeignKey('build.id',
                      ondelete='CASCADE',
                      onupdate='CASCADE'),
           nullable=False,
           index=True),
    Column('cfg_path_id', Integer,
           ForeignKey('cfg_path.id',
                      ondelete='RESTRICT',
                      onupdate='CASCADE'),
           nullable=False),
    Column('order', Integer, nullable=False),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
build_element.create(checkfirst=True)

class BuildElement(aqdbBase):
    pass
mapper(BuildElement,build_element, properties={
    'build'         : relation(Build),
    'cfg_path'      : relation(CfgPath),
    'creation_date' : deferred(build_element.c.creation_date),
    'comments'      : deferred(build_element.c.comments)
})
#unique on host,cfg_path
#unique on build_id/order
#primary key should be host_id/order
#somewhere in this or chost, a change should trigger an
#update_time column on some table to update

s=Session()

def n_of(n,string):
    while n > 0:
        yield ''.join([string,str(n)])
        n-=1


def two_in_each():
    nodelist=[]
    try:
        model  = s.query(Model).filter_by(name='hs21').one()
        syslog = s.query(Service).filter_by(name='syslog').one()
        prod   = s.query(Domain).filter_by(name='production').one()
        stat   = s.query(Status).filter_by(name='prod').one()
    except Exception, e:
        print e
        s.close()
        return

    cmnt   = 'FAKE'

    for b in s.query(Building).all():
        if b.name == 'np':
            continue
        else:
            racks = (Rack(r,'rack',fullname='rack %s'%r,
                          parent=b,comments=cmnt)
                for r in n_of(2,str(b.name)))

        for rack in racks:
            s.save(rack)
            chs = (Chassis(c,'chassis', fullname='chassis %s'%c,
                           parent=rack,comments=cmnt)
                for c in n_of(2,''.join([rack.name,'c'])))

        for ch in chs:
            s.save(ch)
            nodes = (Machine(ch,model,name=nodename,comments=cmnt)
                     for nodename in n_of(12,''.join([ch.name,'n'])))

        for node in nodes:
            try:
                s.save(node)
                nodelist.append(node)
            except Exception, e:
                print e
                s.rollback()
                return


    try:
        s.commit()
    except Exception, e:
        s.rollback()
        print e
        return


    print 'created %s nodes'%(len(nodelist))
    try:
        for node in nodelist:
            h=Host(node,name=node.name,status=stat, domain=prod,comments=cmnt)
            s.save(h)
            s.commit()
    except Exception, e:
        print e
        s.close()
        return
    print 'created %s hosts'%(len(nodelist))

if __name__ == '__main__':
    from aquilon.aqdb.utils.debug import ipshell
    from location import *
    from network import *
    from service import *
    from configuration import *
    from hardware import *
    from interfaces import *
    two_in_each()
