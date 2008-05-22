#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" The module governing tables and objects that represent what are known as
    Services (defined below) in Aquilon.

    Many important tables and concepts are tied together in this module,
    which makes it a bit larger than most. Additionally there are many layers
    at work for things, especially for Host, Service Instance, and Map. The
    reason for this is that breaking each component down into seperate tables
    yields higher numbers of tables, but with FAR less nullable columns, which
    simultaneously increases the density of information per row (and speedy
    table scans where they're required) but increases the 'thruthiness'[1] of
    every row. (Daqscott 4/13/08)
    [1] http://en.wikipedia.org/wiki/Truthiness """
from __future__ import with_statement

import sys
sys.path.append('../..')

import os
import re

from db import *
from name_table import get_name_table, populate_name_table
from aquilon.exceptions_ import ArgumentError

from location import *
from configuration import *
from systems import System, system, BuildItem, Host, host

from sqlalchemy import (Integer, Sequence, String, DateTime, Index,
                        select, insert)
from sqlalchemy.orm import (mapper, relation, deferred, synonym, backref,
                            object_session)

from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.sql import and_, not_

class Service(Base):
    """ SERVICE: a central definition of service is composed of
        a simple name of a service consumable by OTHER hosts. Applications
        that run on a system like ssh are features, not services.

        The config source id/unique column says that there is one and only one
        config source for a service. DNS can not be configured by aqdb AND quattor
        Addtionally, remember that this points to a precise instance of
        aqdb OR quattor as a mechansim. """

    __table__ = Table('service', meta,
                Column('id', Integer, Sequence('service_id_seq'), primary_key=True),
                Column('name', String(64)),
                Column('cfg_path_id', Integer,
                                 ForeignKey('cfg_path.id', name='svc_cfg_pth_fk')),
                UniqueConstraint('name', name='svc_name_uk'),
                UniqueConstraint('cfg_path_id', name='svc_template_uk'))

    cfg_path      = relation(CfgPath, uselist=False, backref='service')
    comments  = deferred(Column('comments', String(255), nullable=True))
    creation_date = deferred(
        Column('creation_date', DateTime, default=datetime.now))



service = Service.__table__
service.create(checkfirst=True)

HostList = get_name_table('HostList','host_list')
host_list = HostList.__table__

class HostListItem(Base):
    __table__ = Table('host_list_item', meta,

    Column('host_list_id', Integer,
           ForeignKey('host_list.id', ondelete='CASCADE', name='hli_hl_fk'),
           primary_key = True),
    Column('host_id', Integer,
           ForeignKey('host.id', ondelete='CASCADE',name='hli_host_fk'),
           nullable=False, primary_key=True),
    Column('position', Integer, nullable=False),
    UniqueConstraint('host_id', name='host_list_uk')) #hosts only on one list?

    creation_date = deferred(Column('creation_date', DateTime, default=datetime.now))
    comments      = deferred(Column('comments', String(255), nullable=True))

    host          = relation(Host)
    hostlist      = relation(HostList)

    def __str__(self):
        return str(self.host.name)

    def __repr__(self):
        return self.__class__.__name__ + " " + str(self.host.name)

HostList.hosts = relation(HostListItem,
                          collection_class=ordering_list('position'),
                            order_by=[HostListItem.__table__.c.position])


class ServiceInstance(Base):
    """ Service instance captures the data around assignment of a system for a
        particular purpose (aka usage). If machines have a 'personality'
        dictated by the application they run """

    __table__ = Table('service_instance',meta,
        Column('id', Integer, Sequence('service_instance_id_seq'),primary_key=True),
        Column('service_id',Integer,
               ForeignKey('service.id', name='svc_inst_svc_fk'), nullable=False),
        Column('host_list_id', Integer,
                ForeignKey('host_list.id', ondelete='CASCADE', name='svc_inst_sys_fk'), nullable=False),
        Column('cfg_path_id', Integer,
            ForeignKey('cfg_path.id', name='svc_inst_cfg_pth_fk'), nullable=False),
        UniqueConstraint('host_list_id',name='svc_inst_host_list_uk'))

    service   = relation(Service, backref='instances')
    host_list = relation(HostList, uselist=False)
    cfg_path  = relation(CfgPath, backref=backref('svc_inst', uselist=False))
    comments  = deferred(Column('comments', String(255), nullable=True))
    creation_date = deferred(
        Column('creation_date', DateTime, default=datetime.now))

    def _client_count(self):
        return object_session(self).query(BuildItem).filter_by(
            cfg_path=self.cfg_path).count()
    client_count = property(_client_count)

    def __repr__(self):
        return '(%s) %s %s'%(self.__class__.__name__ ,
                           self.service.name ,self.host_list.name)
service_instance = ServiceInstance.__table__
service_instance.create(checkfirst=True)

"""
mapper(ServiceInstance,service_instance, properties={
    'service'       : relation(Service, backref='instances'),
    'counter'       : synonym('client_count'),
})
"""


service_map=Table('service_map',meta,
    Column('id', Integer, Sequence('service_map_id_seq'), primary_key=True),
    Column('service_instance_id', Integer,
           ForeignKey('service_instance.id', name='svc_map_svc_inst_fk'),
           nullable=False),
    Column('location_id', Integer,
           ForeignKey('location.id', ondelete='CASCADE', name='svc_map_loc_fk'),
           nullable=False),
    Column('creation_date', DateTime, default=datetime.now),
    Column('comments',String(255), nullable=True),
    UniqueConstraint('service_instance_id','location_id',
                     name='svc_map_loc_inst_uk'))

service_map.create(checkfirst=True)

class ServiceMap(aqdbBase):
    """ Service Map: mapping a service_instance to a location.
        The rows in this table assert that an instance is a valid useable
        default that clients can choose as their provider during service
        autoconfiguration.
    """
    @optional_comments
    def __init__(self, si, loc, *args,**kw):
        if isinstance(si,ServiceInstance):
            self.service_instance = si
        else:
            raise AttributeError('You must supply a valid service instance')
            return
        if isinstance(loc,Location):
            self.location = loc
        else:
            raise AttributeError('You must supply a valid location')
            return
    def _service(self):
        return self.service_instance.service
    service = property(_service)
    def __repr__(self):
        return '(Service Mapping) %s at %s (%s)'%(
            self.service_instance.service, self.location.name, self.location.type)

mapper(ServiceMap,service_map,properties={
    'location'         : relation(Location),
    'service_instance' : relation(ServiceInstance,backref='service_map'),
    'service'          : synonym('_service'),
    'creation_date'    : deferred(service_map.c.creation_date),
    'comments'         : deferred(service_map.c.comments)
})


"""
    Service list item is an individual member of a service list, defined
    in configuration. They represent requirements for baseline archetype
    builds. Think of things like 'dns', 'syslog', etc. that you'd need just
    to get a host up and running...that's what these represent.
"""
service_list_item = Table('service_list_item', meta,
    Column('id', Integer,
           Sequence('service_list_item_id_seq'), primary_key=True),
    Column('service_id', Integer,
           ForeignKey('service.id', name='sli_svc_fk'), nullable=False),
    Column('archetype_id', Integer,
           ForeignKey('archetype.id', name='sli_arctyp_fk'), nullable=False),
    Column('creation_date', DateTime, default=datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('archetype_id','service_id',name='svc_list_svc_uk'))
Index('idx_srvlst_arch_id', service_list_item.c.archetype_id)
service_list_item.create(checkfirst=True)

class ServiceListItem(aqdbBase):
    """ The individual items in a list of required service dependencies """
    @optional_comments
    def __init__(self,archetype,svc):
        if isinstance(archetype,Archetype):
            self.archetype = archetype
        else:
            raise ArgumentError('First argument must be an Archetype')
        if isinstance(svc,Service):
            self.service = svc
        else:
            raise ArgumentError('Second argument must be a Service')

mapper(ServiceListItem,service_list_item,properties={
    'archetype'     : relation(Archetype,backref='service_list'),
    'service'       : relation(Service),
    'creation_date' : deferred(service_list_item.c.creation_date),
    'comments'      : deferred(service_list_item.c.comments)
})

####POPULATION ROUTINES####

def populate_service():
    if empty(service):
        cfg_paths = s.query(CfgPath).filter(
                not_(CfgPath.relative_path.like('%/%'))).join('tld').filter_by(
                type='service').all()
        assert(len(cfg_paths) > 1)

        for i in cfg_paths:
            srv = Service(name=str(i.relative_path),cfg_path=i)
            s.save(srv)
        s.commit()
        print 'populated services'
        s.close()

def populate_service_list():
    s=Session()
    svc = s.query(Service).filter_by(name='afs').one()
    assert(svc)

    arch = s.query(Archetype).filter_by(name='aquilon').one()
    assert(arch)
    if empty(service_list_item):
        sli=ServiceListItem(arch,svc)
        s.save(sli)
        s.commit()
        assert(sli)
        print 'populated service list'
    s.close()

def populate_hli():
    if empty(host):
        print "can't populate host_list_items without hosts."
        return
    elif empty(host_list):
        s=Session()

        hl = HostList(name='test-host-list', comments='FAKE')

        #from shell import ipshell
        #ipshell()

        s.save(hl)
        s.commit()
        assert(hl)

        hosts=s.query(Host).all()
        print '%s hosts is in hosts'%(len(hosts))

        hli=HostListItem(hostlist=hl,host=hosts[1], position=1, comments='FAKE')
        s.save(hli)
        s.commit()
        assert(hli)
        print 'created %s with list items: %s'%(hl,hl.hosts)

if __name__ == '__main__':
    meta.create_all(checkfirst=True)
    s=Session()

    populate_service()
    populate_service_list()
    populate_hli()
