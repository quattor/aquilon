#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''If you can read this, you should be Documenting'''

import datetime

from sys import path,exit
#path.append('./utils')
if __name__ == '__main__':
    path.append('../..')

from DB import meta, engine, Session, aqdbBase
from aquilon.aqdb.utils.debug import ipshell
from aquilon.aqdb.utils.schemahelpers import *

from location import *
location=Table('location', meta, autoload=True)

from sqlalchemy import *
from sqlalchemy.orm import *

service = Table('service',meta,
    Column('id', Integer, primary_key=True, index=True),
    Column('name',String(64), unique=True, index=True),
    Column('cfg_path',String(32), unique=True),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255)))
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
    the burden of naming can be greatly reduced by service lists (which make
    their presence known shortly), though this may be revamped later.
"""
    @optional_comments
    def __init__(self,name):
        self.name=name
        self.cfg_path = 'service/%s'%(self.name)

mapper(Service,service,properties={
    'creation_date' : deferred(service.c.creation_date),
    'comments': deferred(service.c.comments)})

system_type=mk_type_table('system_type', meta)
system_type.create(checkfirst=True)

class SystemType(aqdbType):
    """ System Type is a discrimintor for polymorphic System object/table """
    pass
mapper(SystemType,system_type)
if empty(system_type,engine):
    fill_type_table(system_type,['base_system_type',
                                 'host', 'afs_cell', 'sybase_instance'])

system = Table('system',meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(64), unique=True, index=True),
    Column('type_id', Integer,
           ForeignKey('system_type.id',ondelete='RESTRICT'),
           nullable=False),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255)))
system.create(checkfirst=True)

class System(aqdbBase):
    """ System: a base class which abstracts out the details of between
        all the various kinds of service providers we may use. A System might be
        a host/server/workstation, router, firewall, netapp, etc. Naming this
        is kind of difficult, but "system" seems neutral, and happens not to
        be overloaded by anything I am aware of.

        This is exactly what system does. System_id holds a name, and presents
        an abstract entity that can provide, or utilize services, hardware,
        networks, configuration sources, etc. It's subtyped for flexibilty to
        weather future expansion and enhancement without breaking the
        fundamental archetypes we're building today.

        It is perhaps the most important table so far, and replaces the notion of
        'host' as we've used it in our discussions and designs thus far.
    """
    def __init__(self,cn,*args,**kw):
        if isinstance(cn,str):
            self.name = cn
        else:
            raise ArgumentError("Incorrect name argument %s",cn)
            return
    def type(self):
        return str(self.type)

mapper(System, system, polymorphic_on=system.c.type_id, \
       polymorphic_identity=s.execute(
    "select id from system_type where type='base_system_type'").fetchone()[0],
    properties={
    'creation_date' : deferred(system.c.creation_date),
    'comments': deferred(system.c.comments)})

afs_cell = Table('afs_cell',meta,
    Column('system_id', Integer, ForeignKey('system.id',
                      ondelete='RESTRICT'), primary_key=True))
afs_cell.create(checkfirst=True)

class AfsCell(System):
    """ AfsCell class is an example of a way we'll override system to
        model other types of service providers besides just host
    """
    def __init__(self,name,type,*args,**kw):
        self.name = name
        try:
            self.type = s.execute(
                "select id from system_type where type='afs_cell'").\
                fetchone()[0]
        except Exception,e:
            print e
            return

mapper(AfsCell,afs_cell, inherits=System, polymorphic_identity=s.execute(
                "select id from system_type where type='afs_cell'").\
                fetchone()[0],
       properties={
        'system':relation(System,backref='afs_cell')
})

service_instance = Table('service_instance',meta,
    Column('id', Integer, primary_key=True, index=True),
    Column('service_id',Integer,
           ForeignKey('service.id', ondelete='RESTRICT')),
    Column('system_id', Integer,
           ForeignKey('system.id', ondelete='RESTRICT', onupdate='CASCADE')),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255)),
    UniqueConstraint('service_id','system_id'))

service_instance.create(checkfirst=True)

class ServiceInstance(aqdbBase):
    """ Formerly known as 'provider' service instance captures the data around
    assignment of a system for a particular purpose (aka usage.)
    If machines have a 'personality' dictated by the application they run
    (and they can run and provide more than one, though at the moment, that
    too will be captured by its personality)
    """
    @optional_comments
    def __init__(self,svc,a_sys,*args,**kw):
        if isinstance(svc,Service):
            self.service = svc
        elif isinstance(svc,str):
            try:
                self.service = s.query(Service).filter_by(name=svc).one()
            except Exception, e:
                print "Error looking up service '%s', %s"%(svc,e)
                return
        if isinstance(a_sys,System):
            self.system = a_sys
        elif isinstance(a_sys,str):
            try:
                self.system = s.query(System).filter_by(name=a_sys).one()
            except Exception, e:
                print "Error looking up system '%s', %s"%(a_sys,e)
                return
    def __repr__(self):
        return '%s %s %s'%(self.__class__.__name__ ,
                           str(self.service.name),str(self.system.name))

mapper(ServiceInstance,service_instance, properties={
    'service': relation(Service),
    'system' : relation(System)
})

service_map=Table('service_map',meta,
    Column('id', Integer, primary_key=True),
    Column('service_instance_id', Integer,
           ForeignKey('service_instance.id',
                      ondelete='RESTRICT',
                      onupdate='CASCADE'),
           nullable=False),
    Column('location_id', Integer,
           ForeignKey('location.id',
                      ondelete='CASCADE',
                      onupdate='CASCADE'),
           nullable=False),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments',String(255),nullable=True),
    UniqueConstraint('service_instance_id','location_id'))

service_map.create(checkfirst=True)

class ServiceMap(aqdbBase):
    """ Service Map: mapping a service_instance to a location.
    The rows in this table assert that an instance is a valid useable default
    that clients can choose as their provider during service autoconfiguration
    """
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
    def __repr__(self):
        return 'Service Mapping: %s at %s %s'%(self.service_instance,
                                     self.location.type,self.location)

mapper(ServiceMap,service_map,properties={
    'location':relation(Location),
    'service_instance':relation(ServiceInstance,backref='service_map'),
    'creation_date' : deferred(service_map.c.creation_date),
    'comments': deferred(service_map.c.comments)
})


if __name__ == '__main__':
    if empty(afs_cell,engine):
        a=AfsCell('q.ny','afs_cell')
        s.save(a)
        s.commit()
    else:
        a=s.query(AfsCell).first()

    if empty(service,engine):
        svcs = 'dns','dhcp','quattor','syslog','afs'
        for i in svcs:
            srv = Service(i)
            s.save(srv)
            s.commit()
            del(srv)

    svc=s.query(Service).filter_by(name='afs').one()

    if empty(service_instance,engine):
        si = ServiceInstance(svc,a)
        s.save(si)
        try:
            s.commit()
        except Exception,e:
            s.rollback()
            print e
    else:
        si=s.query(ServiceInstance).first()

    if empty(service_map,engine):
        hub_type=s.query(LocationType).filter_by(type='hub').one()
        loc=s.query(Location).filter(and_(
            location.c.name=='ln',location.c.location_type_id==hub_type.id)).one()
        sm=ServiceMap(si,loc)
        s.save(sm)
        s.commit()
    else:
        sm=s.query(ServiceMap).first()

    print sm
    ipshell()
    exit(0)

#todo: services don't have a unique aqdb or quattor configuration source map
# PATHS SHOULD ALL BE EXTRACTED FOR 2NF AND FLEXIBILITY.
# 'TYPING' provides enhanced search + constraint ability
#quattor config source: has cfg path + domain + quattor server
#service config path could just be:
#   service/<service name>/<instance name>/[ client || server ]

"""
    Consumer captures service selections at the time they are made by building
    a host. This information will be used to generate utilization information
    of service instances, as well as a replay log for service selection when
    rebuilding hosts
"""

"""
consumer = Table('consumer', meta,
    Column('system_id', Integer,
           ForeignKey('system.id',
                      ondelete='CASCADE'),
           primary_key=True),
    Column('service_instance_id', Integer,
           ForeignKey('service_instance.id',
                      ondelete='RESTRICT'),
           nullable=False))


service_list = mk_name_id_table('service_list',meta)

service_list_item = Table('service_list_item', meta,
    Column('id', Integer, primary_key=True),
    Column('service_id',Integer,
           ForeignKey('service.id'), unique=True),
    Column('service_list_id',Integer,
           ForeignKey('service_list.id'), index=True),
    Column('comments', String(255), nullable=True))
"""
