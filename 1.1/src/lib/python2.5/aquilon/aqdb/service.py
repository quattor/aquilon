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

import sys, datetime
sys.path.append('../..')

import os
import re
import exceptions

from db import *
from aquilon.exceptions_ import ArgumentError

from location import *
from network import DnsDomain,dns_domain
from hardware import Machine, machine, Status, status
from auth import UserPrincipal,user_principal

import configuration
from configuration import *
##import * for all the table definitions...

from sqlalchemy import Integer, Sequence, String, Table, DateTime, Index
from sqlalchemy import select, insert
from sqlalchemy.orm import mapper, relation, deferred, synonym, backref, object_session
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.sql import and_, not_

service = Table('service',meta,
    Column('id', Integer, Sequence('service_id_seq'), primary_key=True),
    Column('name',String(64)),
    Column('cfg_path_id', Integer, ForeignKey('cfg_path.id')),
    Column('creation_date', DateTime, default=datetime.datetime.now),
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
        the burden of naming can be greatly reduced by service lists (which make
        their presence known shortly), though this may be revamped later. """

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

mapper(Service,service,properties={
    'cfg_path'      : relation(CfgPath,backref='service'),
    'creation_date' : deferred(service.c.creation_date),
    'comments'      : deferred(service.c.comments)})

system_type=mk_type_table('system_type', meta)
system_type.create(checkfirst=True)

def get_sys_type_id(typ_nm):
    #stmt="select id from system_type where type='%s'"%(typ_nm)
    sl=select([system_type.c.id],system_type.c.type=='%s'%(typ_nm))
    typ_id = engine.execute(sl).scalar()
    assert(typ_id)
    return typ_id

class SystemType(aqdbType):
    """ System Type is a discrimintor for polymorphic System object/table """
    pass
mapper(SystemType,system_type)
if empty(system_type):
    fill_type_table(system_type,['base_system_type',
                                 'host', 'afs_cell',
                                 'quattor_server',
                                 'sybase_instance'])

system = Table('system',meta,
    Column('id', Integer, Sequence('system_id_seq'), primary_key=True),
    Column('name', String(64)),
    Column('type_id', Integer,
           ForeignKey('system_type.id'), nullable=False),
    #TODO: don't hard code the ID in dns_domain as default
    #This will probably break on Oracle
    Column('dns_domain_id', Integer,
           ForeignKey('dns_domain.id'), nullable=False, default=1),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('name','dns_domain_id','type_id',name='system_name_uk'))
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
    def __init__(self,name,**kw):
        if isinstance (name,str):
            self.name = name.strip().lower()
        else:
            raise ArgumentError('name must be string type')

        if kw.has_key('type'):
            if isinstance (typ,SystemType):
                self.type=typ
            else:
                raise ArgumentError('type argument must be SystemType')
        #polymorphic inheritance should cover this anyway, and I might
        #remove it provided I can validate it's always automated.

        if kw.has_key('dns_domain'):
            if isinstance(kw['dns_domain'],str):
                stmt="select id from dns_domain where name ='%s'"%(
                    kw['dns_domain'])
                self.dns_domain_id = engine.execute(stmt).scalar()
                assert(self.dns_domain_id)
                if not self.dns_domain_id:
                    raise ArgumentError('cant find domain %s'%(dns_domain))
            elif isinstance(kw['dns_domain'], DnsDomain):
                self.dns_domain = kw['dns_domain']
            else:
                raise ArgumentError('You must provide either a string, or a DnsDomain object')
        else:
            raise ArgumentError('you must provide a DNS Domain')

    def _fqdn(self):
        if self.dns_domain:
            return '.'.join([str(self.name),str(self.dns_domain.name)])
        # FIXME: Is it correct for a system to not have dns_domain?  If
        # it does not have one, should this return name + '.' anyway?
        return str(self.name)
    fqdn = property(_fqdn)

mapper(System, system, polymorphic_on=system.c.type_id, \
       polymorphic_identity=get_sys_type_id('base_system_type'),
    properties={
        'type'          : relation(SystemType),
        'dns_domain'    : relation(DnsDomain),
        'creation_date' : deferred(system.c.creation_date),
        'comments'      : deferred(system.c.comments)})

quattor_server = Table('quattor_server',meta,
    Column('id', Integer, ForeignKey('system.id'), primary_key=True),)
quattor_server.create(checkfirst=True)

class QuattorServer(System):
    """ Quattor Servers are a speicalized system to provide configuration
        services for the others on the network. This also helps to
        remove cyclical dependencies of hosts, and domains (hosts must be
        in exaclty one domain, and a domain must have a host as it's server)
    """
    def __init__(self,name,**kw):
        #default dns domain for quattor servers to ms.com
        if not kw.has_key('dns_domain'):
            kw['dns_domain'] = 'ms.com'
        super(QuattorServer, self).__init__(name,**kw)


mapper(QuattorServer,quattor_server,
        inherits=System, polymorphic_identity=get_sys_type_id('quattor_server'),
       properties={'system': relation(System,backref='quattor_server')})

domain = Table('domain', meta,
    Column('id', Integer, Sequence('domain_id_seq'), primary_key=True),
    Column('name', String(32)),
    Column('server_id', Integer, ForeignKey('quattor_server.id'), nullable=False),
    Column('compiler', String(255), nullable=False,
           default='/ms/dist/elfms/PROJ/panc/7.2.9/bin/panc'),
    Column('owner_id', Integer,
           ForeignKey('user_principal.id'), nullable=False,
           default=get_sys_type_id('quattor_server')),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('name',name='domain_uk'))
domain.create(checkfirst=True)

class Domain(aqdbBase):
    """ Domain is to be used as the top most level for path traversal of the SCM
            Represents individual config repositories
    """
    def __init__(self, name, server, owner, **kw):
        self.name=name.strip().lower()
        if isinstance(server,QuattorServer):
            self.server = server
        else:
            raise ArgumentError('second argument must be a Quattor Server')
        if isinstance(owner, UserPrincipal):
            self.owner = owner
        else:
            raise ArgumentError('third argument must be a Kerberos Principal')

        if kw.has_key('compiler'):
            self.compiler = kw.pop('compiler')
        else:
            self.compiler = '/ms/dist/elfms/PROJ/panc/7.2.9/bin/panc'

mapper(Domain,domain,properties={
    'server':           relation(QuattorServer,backref='domain'),
    'owner':            relation(UserPrincipal,remote_side=user_principal.c.id),
    'creation_date':    deferred(domain.c.creation_date),
    'comments':         deferred(domain.c.comments)})

host=Table('host', meta,
    Column('id', Integer, ForeignKey('system.id'), primary_key=True),
    Column('machine_id', Integer, ForeignKey('machine.id')),
    Column('domain_id', Integer, ForeignKey('domain.id')),
    Column('archetype_id',Integer, ForeignKey('archetype.id'),nullable=False),
    Column('status_id', Integer, ForeignKey('status.id')),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
host.create(checkfirst=True)

class Host(System):
    """ Here's our most common kind of System, the Host. Putting a physical
        machine into a chassis and powering it up leaves it in a state with a
        few more attributes not filled in: what Domain configures this host?
        What is the build/mcm 'status'? If Ownership is captured, this is the
        place for it.
    """
    @optional_comments
    def __init__(self,mach,dom,stat,**kw):

        if isinstance(dom,Domain):
            self.domain = dom
        else:
            raise ArgumentError('second argument must be a valid domain')

        if isinstance(stat, Status):
            self.status = stat
        else:
            raise ArgumentError('third argument must be a valid status')

        if isinstance(mach,Machine):
            self.machine=mach
        if kw.has_key('name'):
            name = kw.pop('name')
            if isinstance(name,str):
                self.name=name.strip().lower()
            else:
                raise ArgumentError("Host name must be type 'str'")
        else:
            self.name=kw.pop('name',mach.name)

        arch=kw.pop('archetype','aquilon')
        self.archetype_id=id_getter(archetype,archetype.c.name,arch)
        assert(self.archetype_id)

        if kw.has_key('dns_domain'):
            dns_domain = kw.pop('dns_domain')
            if isinstance(dns_domain, DnsDomain):
                self.dns_domain = dns_domain
            else:
                raise ArgumentError("dns_domain must be a valid DnsDomain")

    def _get_location(self):
        return self.machine.location
    location = property(_get_location) #TODO: make these synonms?

    def _sysloc(self):
        return self.machine.location.sysloc()
    sysloc = property(_sysloc)

    def __repr__(self):
        return 'Host %s'%(self.name)
#Host mapper deferred for ordering list to build_item...

build_item = Table('build_item', meta,
    Column('id', Integer, Sequence('build_item_id_seq'), primary_key=True),
    Column('host_id', Integer,
           ForeignKey('host.id'), nullable=False),
    Column('cfg_path_id', Integer,
           ForeignKey('cfg_path.id'),
           nullable=False),
    Column('position', Integer, nullable=False),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('host_id','cfg_path_id',name='host_tmplt_uk'),
    UniqueConstraint('host_id','position',name='host_position_uk'))
build_item.create(checkfirst=True)

class BuildItem(aqdbBase):
    """ Identifies the build process of a given Host.
        Parent of 'build_element' """
    @optional_comments
    def __init__(self,host,cp,position):
        if isinstance(host,Host):
            self.host=host
        else:
            msg = 'Build object requires a Host for its constructor'
            raise ArgumentError(msg)

        if isinstance(cp,CfgPath):
            self.cfg_path=cp
        else:
            msg = 'Build Item requires a Config Path as its second arg'
            raise ArgumentError(msg)
        if isinstance(position,int):
            self.position=position
        else:
            msg='Build Item only accepts integer as its third argument'
            raise(msg)

    def __repr__(self):
        return '%s: %s'%(self.host.name,self.cfg_path)

mapper(BuildItem,build_item,properties={
    'host'          : relation(Host),
    'cfg_path'      : relation(CfgPath),
    'creation_date' : deferred(build_item.c.creation_date),
    'comments'      : deferred(build_item.c.comments)})

#Uses Ordering List, an advanced data mapping pattern for this kind of thing
#more at http://www.sqlalchemy.org/docs/04/plugins.html#plugins_orderinglist
mapper(Host, host, inherits=System,
       polymorphic_identity=get_sys_type_id('host'),
    properties={
        'system'        : relation(System),
        # Not 100% sure why the uselist=False needs to be on the backref here,
        # instead of in the relation.  See the "One To One" section of the docs.
        # http://www.sqlalchemy.org/docs/04/mappers.html
        'machine'       : relation(Machine,
                                   backref=backref('host', uselist=False)),
        'domain'        : relation(Domain,
                                   primaryjoin=host.c.domain_id==domain.c.id,
                                   uselist=False,
                                   backref=backref('hosts')),
        #TODO: Archetype (for base/final)
        #TODO: synonym for location, sysloc, fqdn (in system)
        'status'        : relation(Status),
        'templates'     : relation(BuildItem,
                                   collection_class=ordering_list('position'),
                                   order_by=[build_item.c.position]),
        'creation_date' : deferred(host.c.creation_date),
        'comments'      : deferred(host.c.comments)
})

afs_cell = Table('afs_cell',meta,
    Column('system_id', Integer, ForeignKey('system.id',
                                            ondelete='CASCADE'),
           primary_key=True))
afs_cell.create(checkfirst=True)

class AfsCell(System):
    """ AfsCell class is an example of a way we'll override system to
        model other types of service providers besides just host
    """
    @optional_comments
    def __init__(self,name,**kw):
        if isinstance(name,str):
            name=name.strip().lower()
            #FIX ME: this was a rush job to get it working before I leave for
            #someone please implement this with a better message
            #m=re.match("^([a-z]{1})\.([a-z]{2})$",name)
            #m.groups should equal 2.
            if name.count('.') != 1:
                msg="""
                    Names of afs cell's must match the pattern 'X.YZ'
                    where X.YZ are all single alphabetic characters, and YZ
                    must match the name of a valid HUB or BUILDING. """
                    ###FIX ME: BROKER HAS TO ENFORCE THIS (NO SESSION CALLS ARE
                    ###        ALLOWED IN __init__() METHODS.)
                    ### Long term, a check constraint would be better to keep
                    ### bad data out of the DB, but also afs cell creation will
                    ### be highly restricted.
                raise ArgumentError(msg.strip())
                return
        else:
            msg="name of Afs Cell must be a string, received '%s', %s"%(
                name,type(name))
            raise ArgumentError(msg)

        if not kw.has_key('dns_domain'):
            kw['dns_domain'] = 'ms.com'

        super(AfsCell, self).__init__(name,**kw)
        ###TODO: Would it be ok to make a service instance here? a cell without
        ###   one really wouldn't make a whole lot of sense...

mapper(AfsCell,afs_cell,
        inherits=System, polymorphic_identity=get_sys_type_id('afs_cell'),
       properties={
        'system' : relation(System, uselist=False, backref='afs_cell')})

service_instance = Table('service_instance',meta,
    Column('id', Integer, Sequence('service_instance_id_seq'),primary_key=True),
    Column('service_id',Integer, ForeignKey('service.id')),
    Column('system_id', Integer, ForeignKey('system.id')),
    Column('cfg_path_id', Integer, ForeignKey('cfg_path.id')),
    Column('creation_date', DateTime, default=datetime.datetime.now),
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
    Column('creation_date', DateTime, default=datetime.datetime.now),
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
    Column('creation_date', DateTime, default=datetime.datetime.now),
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

def create_domains():
    s=Session()
    if empty(quattor_server):
        qs=QuattorServer('quattorsrv')
        s.save(qs)
        s.commit()
    else:
        qs=s.query(QuattorServer).filter_by(name='quattorsrv').one()

    njw = s.query(UserPrincipal).filter_by(name='njw').one()
    quattor = s.query(UserPrincipal).filter_by(name='quattor').one()

    if empty(domain):
        p = Domain('production', qs, njw,
                comments='The master production area')
        q = Domain('qa', qs, quattor, comments='Do your testing here')
        s.save_or_update(p)
        s.save_or_update(q)

        s.commit()
        print 'created production and qa domains'
        s.close()

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
            srv = Service(i)
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
    s=Session()
    create_domains()
    d=s.query(Domain).first()
    assert(d)

    populate_service()
    #assert for afs service within the next function call...
    populate_service_list()
    #TODO: assert, and MAKE NOSE testFunctions out of all these
