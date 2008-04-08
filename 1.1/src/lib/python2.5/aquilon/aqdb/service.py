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
    Services (defined below) in Aquilon """
from __future__ import with_statement

import sys, datetime
sys.path.append('../..')

from db import *

from location import *
location=Table('location', meta, autoload=True)

from network import DnsDomain
dns_domain=Table('dns_domain', meta, autoload=True)

from hardware import Machine, Status
machine=Table('machine', meta, autoload=True)
status = Table('status', meta, autoload=True)

from auth import UserPrinciple
user_principle = Table('user_principle', meta, autoload=True)
from configuration import ServiceList
service_list = Table('service_list', meta, autoload=True)

from sqlalchemy import Integer, Sequence, String, Table, DateTime, Index
from sqlalchemy.orm import mapper, relation, deferred, synonym, backref
from sqlalchemy.sql import and_

service = Table('service',meta,
    Column('id', Integer, Sequence('service_id_seq'), primary_key=True),
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
                                 'host', 'afs_cell',
                                 'quattor_server',
                                 'sybase_instance'])

system = Table('system',meta,
    Column('id', Integer, Sequence('system_id_seq'), primary_key=True),
    Column('name', String(64), unique=True, index=True),
    Column('type_id', Integer,
           ForeignKey('system_type.id'),
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
    @optional_comments
    def __init__(self,cn,*args,**kw):
        if isinstance(cn,str):
            self.name = cn
        else:
            raise ArgumentError("Incorrect name argument %s",cn)
            return
    #def type(self):
    #    return str(self.type)

mapper(System, system, polymorphic_on=system.c.type_id, \
       polymorphic_identity=s.execute(
    "select id from system_type where type='base_system_type'").fetchone()[0],
    properties={
        'type':relation(SystemType),
        'creation_date' : deferred(system.c.creation_date),
        'comments': deferred(system.c.comments)})

quattor_server = Table('quattor_server',meta,
    Column('id', Integer, ForeignKey('system.id'), primary_key=True),)
quattor_server.create(checkfirst=True)

class QuattorServer(System):
    """ Quattor Servers are a speicalized system to provide configuration
        services for the others on the network. This also helps to
        remove cyclical dependencies of hosts, and domains (hosts must be
        in exaclty one domain, and a domain must have a host as it's server)
    """
    pass

mapper(QuattorServer,quattor_server,
        inherits=System, polymorphic_identity=s.execute(
          "select id from system_type where type='quattor_server'").fetchone()[0],
       properties={ 'system': relation(System,backref='quattor_server')})

""" TODO: a better place for dns-domain. We'll need to flesh out DNS
        support within aqdb in the coming weeks after the handoff, but for now,
        it's an innocuous place since hosts can only be in one domain
    """
domain = Table('domain', meta,
    Column('id', Integer, Sequence('domain_id_seq'), primary_key=True),
    Column('name', String(32), unique=True, index=True),
    Column('server_id', Integer,
           ForeignKey('quattor_server.id'), nullable=False),
    Column('compiler', String(255), nullable=False,
           default='/ms/dist/elfms/PROJ/panc/7.2.9/bin/panc'),
    Column('dns_domain_id', Integer,
           ForeignKey('dns_domain.id'), nullable=False, default=2),
    Column('owner_id', Integer,
           ForeignKey('user_principle.id'),nullable=False,
           default=s.execute(
    "select id from user_principle where name='quattor'").fetchone()[0]),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
domain.create(checkfirst=True)

class Domain(aqdbBase):
    """ Domain is to be used as the top most level for path traversal of the SCM
            Represents individual config repositories
    """
    def __init__(self, name, server , **kw):
        self.name=name.strip().lower()
        if isinstance(server,QuattorServer):
            self.server = server
        else:
            raise ArgumentError('second argument must be a Quattor Server')

        self.dns_domain=s.query(DnsDomain).\
            filter_by(name=(kw.pop('dns-domain', 'one-nyp'))).one()

        self.compiler=kw.pop('compiler',
                             '/ms/dist/elfms/PROJ/panc/7.2.9/bin/panc')

        self.owner=s.query(UserPrinciple).\
            filter_by(name=(kw.pop('owner','quattor'))).one()

mapper(Domain,domain,properties={
    'server':           relation(QuattorServer,backref='domain'),
    'dns_domain':       relation(DnsDomain),
    'owner':            relation(UserPrinciple,remote_side=user_principle.c.id),
    'creation_date':    deferred(domain.c.creation_date),
    'comments':         deferred(domain.c.comments)})

host=Table('host', meta,
    Column('id', Integer, ForeignKey('system.id'), primary_key=True),
    Column('machine_id', Integer, ForeignKey('machine.id')),
    Column('domain_id', Integer, ForeignKey('domain.id')),
    Column('status_id', Integer, ForeignKey('status.id')),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
host.create(checkfirst=True)

class Host(System):
    """  """
    @optional_comments
    def __init__(self,machine,**kw):
        s = Session()
        if isinstance(machine,Machine):
            self.machine=machine
        self.name=kw.pop('name',machine.name)
        self.domain=kw.pop('domain',
                           s.query(Domain).filter_by(name='qa').one())
        self.status=kw.pop('status',
                           s.query(Status).filter_by(name='build').one())
        s.close()

    def _get_location(self):
        return self.machine.location
    location = property(_get_location)

    def _sysloc(self):
        return self.machine.location.sysloc()
    sysloc = property(_sysloc)

    def _fqdn(self):
        return '.'.join([str(self.name),str(self.domain.dns_domain)])
    fqdn = property(_fqdn)

    def __repr__(self):
        return 'Host %s'%(self.name)

mapper(Host, host, inherits=System, polymorphic_identity=s.execute(
           "select id from system_type where type='host'").fetchone()[0],
    properties={
        'system'        : relation(System),
        'machine'       : relation(Machine,backref='host'),
        'domain'        : relation(Domain,
                                   primaryjoin=host.c.domain_id==domain.c.id,
                                   backref=backref('hosts')),
        'status'        : relation(Status),
        'creation_date' : deferred(host.c.creation_date),
        'comments'      : deferred(host.c.comments)
})

afs_cell = Table('afs_cell',meta,
    Column('system_id', Integer, ForeignKey('system.id'), primary_key=True))
afs_cell.create(checkfirst=True)

class AfsCell(System):
    """ AfsCell class is an example of a way we'll override system to
        model other types of service providers besides just host
    """
    pass

mapper(AfsCell,afs_cell,
        inherits=System, polymorphic_identity=s.execute(
           "select id from system_type where type='afs_cell'").fetchone()[0],
       properties={'system':relation(System,backref='afs_cell')})

service_instance = Table('service_instance',meta,
    Column('id', Integer, Sequence('service_instance_id_seq'),primary_key=True),
    Column('service_id',Integer, ForeignKey('service.id')),
    Column('system_id', Integer, ForeignKey('system.id')),
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
    'system' : relation(System),
    'creation_date' : deferred(service_instance.c.creation_date),
    'comments': deferred(service_instance.c.comments)
})

service_map=Table('service_map',meta,
    Column('id', Integer, Sequence('service_map_id_seq'), primary_key=True),
    Column('service_instance_id', Integer,
           ForeignKey('service_instance.id'),
           nullable=False),
    Column('location_id', Integer,
           ForeignKey('location.id', ondelete='CASCADE'),
           nullable=False),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments',String(255),nullable=True),
    UniqueConstraint('service_instance_id','location_id'))

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
    def __repr__(self):
        return 'Service Mapping: %s at %s %s'%(self.service_instance,
                                     self.location.type,self.location)

mapper(ServiceMap,service_map,properties={
    'location':relation(Location),
    'service_instance':relation(ServiceInstance,backref='service_map'),
    'creation_date' : deferred(service_map.c.creation_date),
    'comments': deferred(service_map.c.comments)
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
    Column('service_id',Integer,
           ForeignKey('service.id'), unique=True),
    Column('service_list_id',Integer,
           ForeignKey('service_list.id')),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
Index('idx_srv_list_item_list_id', service_list_item.c.service_list_id)
service_list_item.create(checkfirst=True)

class ServiceListItem(aqdbBase):
    """ The individual items in a list of required service dependencies """
    @optional_comments
    def __init__(self,svc_list,svc):
        self.service_list = svc_list
        self.service = svc
    def __repr__(self):
        return '(service list item) %s'%(self.service.name)

mapper(ServiceListItem,service_list_item,properties={
    'service_list': relation(ServiceList, backref='items'),
    'service': relation(Service),
    'creation_date' : deferred(service_list_item.c.creation_date),
    'comments': deferred(service_list_item.c.comments)
})

####POPULATION ROUTINES####

def create_domains():
    s=Session()
    if empty(quattor_server):
        qs=QuattorServer('quattorsrv')
        s.save(qs)
        s.commit()
    else:
        qs=s.query(QuattorServer).filter_by(name='quattorsrv').one()

    if empty(domain,engine):
        p = Domain('production',qs, owner='njw', comments='The master production area')
        q = Domain('qa',qs, owner='quattor', comments='Do your testing here')
        s.save_or_update(p)
        s.save_or_update(q)

        s.commit()
        print 'created production and qa domains'

def populate_all_service_tables():
    if empty(afs_cell,engine):
        for c in ['a.ny','b.ny','c.ny','q.ny','q.ln']:
            a=AfsCell(c+'.ms.com','afs_cell')
            s.save(a)
        s.commit()
        print 'created afs cells'
    else:
        a=s.query(AfsCell).first()

    if empty(service,engine):
        svcs = 'dns','dhcp','quattor','syslog','afs'
        for i in svcs:
            srv = Service(i)
            s.save(srv)
            s.commit()
        print 'populated services'

    svc=s.query(Service).filter_by(name='afs').one()

    if empty(service_instance,engine):
        si = ServiceInstance(svc,a)
        s.save(si)
        try:
            s.commit()
        except Exception,e:
            s.rollback()
            print e
        print 'populated a test service instance (%s)'%(si)
    else:
        si=s.query(ServiceInstance).first()

    if empty(service_map,engine):
        hub_type=s.query(LocationType).filter_by(type='hub').one()
        loc=s.query(Location).filter(and_(
            location.c.name=='ln',location.c.location_type_id==hub_type.id)).one()
        sm=ServiceMap(si,loc)
        s.save(sm)
        s.commit()
        print 'populated service map with a sample'
    else:
        sm=s.query(ServiceMap).first()

    if empty(service_list,engine):
        sl=ServiceList('aquilon')
        s.save(sl)
        s.commit()

        svc=s.query(Service).filter_by(name='syslog').one()

        sli=ServiceListItem(sl,svc)
        s.save(sli)
        s.commit()
        print 'populated service list'

if __name__ == '__main__':
    #from aquilon.aqdb.utils.debug import ipshell

    create_domains()
    d=s.query(Domain).first()
    assert(d)

    populate_all_service_tables()
