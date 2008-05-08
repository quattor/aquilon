#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" For Systems and related objects """
import sys
sys.path.append('../..')

from db import *
from configuration import *
from subtypes import SystemType, system_type, get_sys_type_id
from network import DnsDomain, dns_domain
from hardware import Machine, machine, Status, status
from auth import UserPrincipal, user_principal
from aquilon.exceptions_ import ArgumentError

from sqlalchemy.orm import (mapper, relation, deferred, backref)
from sqlalchemy.ext.orderinglist import ordering_list

system = Table('system', meta,
    Column('id', Integer, Sequence('system_id_seq'), primary_key=True),
    Column('name', String(64)),
    Column('type_id', Integer,
           ForeignKey('system_type.id', name='system_sys_typ_fk'),
           nullable=False),
    Column('dns_domain_id', Integer,
           ForeignKey('dns_domain.id', name='sys_dns_fk'), nullable=False,
           default=id_getter(dns_domain,dns_domain.c.name,'ms.com')),
    Column('creation_date', DateTime, default=datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('name','dns_domain_id','type_id',name='system_name_uk'))

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
    __table__ = system
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
    Column('id', Integer,
           ForeignKey('system.id', ondelete='CASCADE', name='qs_system_fk'),
           primary_key=True))

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
        inherits=System,
        polymorphic_identity=get_sys_type_id('quattor_server'), properties={
        'system'        : relation(System, uselist=False,
                                   backref='quattor_server'),
})


domain = Table('domain', meta,
    Column('id', Integer, Sequence('domain_id_seq'), primary_key=True),
    Column('name', String(32)),
    Column('server_id', Integer,
           ForeignKey('quattor_server.id',
                      name = 'domain_qs_fk'), nullable=False),
    Column('compiler', String(255), nullable=False,
           default='/ms/dist/elfms/PROJ/panc/7.2.9/bin/panc'),
    Column('owner_id', Integer,
           ForeignKey('user_principal.id'), nullable=False,
           default=get_sys_type_id('quattor_server')),
    Column('creation_date', DateTime, default=datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('name',name='domain_uk'))

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
    'server'        : relation(QuattorServer,backref='domain'),
    'owner'         : relation(UserPrincipal,remote_side=user_principal.c.id),
    'creation_date' : deferred(domain.c.creation_date),
    'comments'      : deferred(domain.c.comments)})

host=Table('host', meta,
    Column('id', Integer, ForeignKey('system.id',
                                     ondelete='CASCADE',
                                     name='host_system_fk'), primary_key=True),
    Column('machine_id', Integer,
           ForeignKey('machine.id', name='host_machine_fk'), nullable=False),
    Column('domain_id', Integer,
           ForeignKey('domain.id', name='host_domain_fk'), nullable=False),
    Column('archetype_id',Integer,
           ForeignKey('archetype.id', name='host_arch_fk'), nullable=False),
    Column('status_id', Integer,
           ForeignKey('status.id', name='host_status_fk'), nullable=False))


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
           ForeignKey('host.id', ondelete='CASCADE', name='build_item_host_fk'),
           nullable=False),
    Column('cfg_path_id', Integer,
           ForeignKey('cfg_path.id',
                      name='build_item_cfg_path_fk'),
           nullable=False),
    Column('position', Integer, nullable=False),
    Column('creation_date', DateTime, default=datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('host_id','cfg_path_id',name='host_tmplt_uk'),
    UniqueConstraint('host_id','position',name='host_position_uk'))


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

mapper(Host, host, inherits=System,
       polymorphic_identity=get_sys_type_id('host'),
    properties={
        'system'        : relation(System),
        'machine'       : relation(Machine,
                                   backref=backref('host', uselist=False)),
        'domain'        : relation(Domain,
                                   primaryjoin=host.c.domain_id==domain.c.id,
                                   uselist=False,
                                   backref=backref('hosts')),
        'archetype'     : relation(Archetype, uselist=False),
        'status'        : relation(Status),
        'templates'     : relation(BuildItem,
                                   collection_class=ordering_list('position'),
                                   order_by=[build_item.c.position])
#TODO: synonym for location, sysloc, fqdn (in system)
})

host_list = Table('host_list', meta,
    Column('id', Integer, ForeignKey('system.id',
                                     ondelete='CASCADE',
                                     name='host_list_fk'),
           primary_key=True))

class HostList(System):
    """ The default system type used for ServiceInstances will be this
        data structure, a list of hosts. """

    def __init__(self,name,**kw):
        #default dns domain for host lists to ms.com (for now)
        if not kw.has_key('dns_domain'):
            kw['dns_domain'] = 'ms.com'
        super(HostList, self).__init__(name,**kw)



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

    creation_date = get_date_col()
    comments      = get_comment_col()

    host          = relation(Host)
    hostlist      = relation(HostList)

    def __repr__(self):
        return self.__class__.__name__ + " " + str(self.host.name)


mapper(HostList, host_list, inherits=System,
       polymorphic_identity=get_sys_type_id('host_list'), properties = {
        'system' : relation(System, uselist=False, backref='host_list'),
        'hosts'  : relation(HostListItem,
                            collection_class=ordering_list('position'),
                            order_by=[HostListItem.__table__.c.position]),
})

afs_cell = Table('afs_cell',meta,
    Column('system_id', Integer,
           ForeignKey('system.id',
                      name='afs_system_fk', ondelete='CASCADE'),
           primary_key=True))


class AfsCell(System):
    """ AfsCell class is an example of a way we'll override system to
        model other types of service providers besides just host
    """
    @optional_comments
    def __init__(self,name,**kw):
        if isinstance(name,str):
            name=name.strip().lower()
            #FIX ME: implement with a better message
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


def populate_quattor_srv():
    s=Session()
    if empty(quattor_server):
        qs=QuattorServer(name='oziyp2', dns_domain='ms.com', comments='FAKE')
        s.save(qs)
        s.commit()
    else:
        qs=s.query(QuattorServer).filter_by(name='oziyp2').one()

def populate_domains():
    if empty(domain):
        s=Session()

        njw = s.query(UserPrincipal).filter_by(name='njw').one()
        assert(njw)
        cdb = s.query(UserPrincipal).filter_by(name='cdb').one()
        assert(cdb)
        qs = s.query(QuattorServer).first()
        assert(qs)

        p = Domain('production', qs, njw, comments='The master production area')
        q = Domain('qa', qs, cdb, comments='Do your testing here')

        s.save_or_update(p)
        s.save_or_update(q)

        s.commit()
        d=s.query(Domain).first()
        assert(d)
        print 'created production and qa domains'
        s.close()


def populate_hli():
    if empty(host):
        print "can't populate host_list_items without hosts."
        return
    elif empty(host_list):
        s=Session()
        from shell import ipshell
        hl = HostList(name='test-host-list', dns_domain='ms.com',
                      comments='FAKE')
        s.commit()
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

    populate_quattor_srv()
    populate_domains()
    populate_hli()
