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
from aquilon.exceptions_ import ArgumentError

from location import *
from configuration import *
from systems import System,system

from sqlalchemy import (Integer, Sequence, String, DateTime, Index,
                        select, insert)
from sqlalchemy.orm import (mapper, relation, deferred, synonym, backref,
                            object_session)

from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.sql import and_, not_

service = Table('service', meta,
    Column('id', Integer, Sequence('service_id_seq'), primary_key=True),
    Column('name', String(64)),
    Column('cfg_path_id', Integer, ForeignKey('cfg_path.id')),
    Column('creation_date', DateTime, default=datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('name',name='svc_name_uk'),
    UniqueConstraint('cfg_path_id',name='svc_template_uk'))
service.create(checkfirst=True)

class Service(aqdbBase):
    """ SERVICE: a central definition of service is composed of
        a simple name of a service consumable by OTHER hosts. Applications
        that run on a system like ssh are features, not services.

        The config source id/unique column says that there is one and only one
        config source for a service. DNS can not be configured by aqdb AND quattor
        Addtionally, remember that this points to a precise instance of
        aqdb OR quattor as a mechansim.

        We're not currently subtyping or 'grading' services with 'prod/qa/dev' etc.
        It would have to be accomplished with the name, i.e. production-dns, and
        the burden of naming can be greatly reduced by service lists,
        though this may be revamped later. """

    @optional_comments
    def __init__(self,name):
        self.name=name.strip().lower()

        service_id=engine.execute(
            select([cfg_tld.c.id],cfg_tld.c.type=='service')).fetchone()[0]
        if not service_id:
            raise ArgumentError('Service TLD is undefined')

        result=engine.execute(
            """SELECT id FROM cfg_path WHERE
                cfg_tld_id=%s
                AND relative_path = '%s' """%(service_id,self.name)).fetchone()
        if result:
            self.cfg_path_id = result[0]
        else:
            print "No cfg path for service %s, creating..."%(self.name)
            i=cfg_path.insert()
            result=i.execute(relative_path=self.name,
                              cfg_tld_id=service_id,
                              comments='autocreated')
            self.cfg_path_id=result.last_inserted_ids()[0]
    """ We're being nice here. Don't know if we should be, but wanted to show
        another way around the problem we had with using session in the init
        functions. The line WAS:
            raise ArgumentError('no cfg path for %s'%(self.name))

        The path on filesystem is not created here like I did for the
        afs cells in all_cells() in population_scripts (did em manaully) """

mapper(Service, service, properties={
    'cfg_path'      : relation(CfgPath,backref='service'),
    'creation_date' : deferred(service.c.creation_date),
    'comments'      : deferred(service.c.comments)})


service_instance = Table('service_instance',meta,
    Column('id', Integer, Sequence('service_instance_id_seq'),primary_key=True),
    Column('service_id',Integer, ForeignKey('service.id')),
    Column('system_id', Integer, ForeignKey('system.id',ondelete='CASCADE')),
    Column('cfg_path_id', Integer, ForeignKey('cfg_path.id')),
    Column('creation_date', DateTime, default=datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('service_id','system_id',name='svc_inst_system_uk'))

service_instance.create(checkfirst=True)

class ServiceInstance(aqdbBase):
    """ Service instance captures the data around assignment of a system for a
        particular purpose (aka usage)
        If machines have a 'personality' dictated by the application they run
    """
    @optional_comments
    def __init__(self,svc,a_sys,*args,**kw):
        if isinstance(svc,Service):
            self.service = svc
        else:
            raise ArgumentError('First argument must be a valid Service')
        if isinstance(a_sys,System):
            self.system = a_sys
        else:
            raise ArgumentError('Second Argument must be a valid System')

        path='%s/%s'%(self.service.name,self.system.fqdn)

        service_id=engine.execute(
                select([cfg_tld.c.id],cfg_tld.c.type=='service')).fetchone()[0]
        if not service_id:
            raise ArgumentError('Service TLD is undefined')

        result=engine.execute(
                """ SELECT id FROM cfg_path WHERE
                    cfg_tld_id=%s
                    AND relative_path = '%s' """%(service_id,path)).fetchone()
        if result:
            self.cfg_path_id=result[0]
        else:
            i=cfg_path.insert()
            result=i.execute(relative_path=path,
                              cfg_tld_id=service_id,
                              comments='autocreated')
            if result:
                self.cfg_path_id=result.last_inserted_ids()[0]
            else:
                raise ArgumentError('unable to create cfg path')
            #TODO: a better exception and a much better message

    def _client_count(self):
        return object_session(self).query(BuildItem).filter_by(
            cfg_path=self.cfg_path).count()
    client_count = property(_client_count)

    def __repr__(self):
        return '(%s) %s %s'%(self.__class__.__name__ ,
                           self.service.name ,self.system.name)

mapper(ServiceInstance,service_instance, properties={
    'service'       : relation(Service),
    'system'        : relation(System, uselist=False, backref='svc_inst'),
    'cfg_path'      : relation(CfgPath, uselist=False, backref='svc_inst'),
    'counter'       : synonym('client_count'),
    'creation_date' : deferred(service_instance.c.creation_date),
    'comments'      : deferred(service_instance.c.comments)
})

service_map=Table('service_map',meta,
    Column('id', Integer, Sequence('service_map_id_seq'), primary_key=True),
    Column('service_instance_id', Integer,
           ForeignKey('service_instance.id'),
           nullable=False),
    Column('location_id', Integer,
           ForeignKey('location.id', ondelete='CASCADE'),
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
    Column('service_id', Integer, ForeignKey('service.id')),
    Column('archetype_id', Integer, ForeignKey('archetype.id'), nullable=False),
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
        if cfg_paths:
            svcs = [str(cp.relative_path) for cp in cfg_paths]
        else:
            svcs = ['dns', 'dhcp', 'syslog', 'afs']
        for i in svcs:
            srv = Service(name=i)
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

if __name__ == '__main__':
    meta.create_all(checkfirst=True)
    s=Session()

    populate_service()
    populate_service_list()
