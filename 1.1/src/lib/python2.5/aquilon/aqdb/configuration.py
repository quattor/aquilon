#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" The tables/objects/mappings related to configuration in aquilon """

import datetime

import sys
sys.path.append('../..')

from db import *

from aquilon import const

from aquilon.aqdb.utils.exceptions_ import NoSuchRowException

from sqlalchemy import Table, Integer, Sequence, String, ForeignKey
from sqlalchemy.orm import mapper, relation, deferred

from network import DnsDomain
dns_domain=Table('dns_domain', meta, autoload=True)


import os
osuser = os.environ.get('USER')
qdir = os.path.join( '/var/tmp', osuser, 'quattor/template-king' )
const.cfg_base=os.path.join('/var/tmp', osuser, 'quattor/template-king')



def splitall(path):
    """
        Split a path into all of its parts.
    """
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path:
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts

cfg_tld = mk_type_table('cfg_tld',meta)
cfg_tld.create(checkfirst=True)

class CfgTLD(aqdbType):
    """ Configuration Top Level Directory or 'cfg_tld' are really the high level
        namespace categories, or the directories in /var/quattor/template-king
            base      (only one for now)
            os        (major types (linux,solaris) prefabricated)
            hardware  entered by model (vendors + types prefabricated)
            services
            feature  also need groups
            final     (only one for now)
            personality is really just app (or service if its consumable too)
    """
    pass
mapper(CfgTLD, cfg_tld, properties={
    'creation_date' : deferred(cfg_tld.c.creation_date)})


""" Config Source Type are labels for the 'type' attribute in the
    config_source table, supplied to satisfy 2NF. Currently we support
    2 types of configuration, aqdb, and quattor. Later, we'll be supporting
    a new type, 'Cola'
"""
cfg_source_type = mk_type_table('cfg_source_type',meta)
meta.create_all()


class CfgSourceType(aqdbType):
    """ Config Source Type are labels for the 'type' attribute in the
        config_source table, supplied to satisfy 2NF. Currently we support
        2 types of configuration, aqdb, and quattor. Later, we'll be supporting
        a new type, 'Cola'
    """
mapper(CfgSourceType, cfg_source_type, properties={
    'creation_date' : deferred(cfg_source_type.c.creation_date)})


cfg_path = Table('cfg_path',meta,
    Column('id', Integer, Sequence('cfg_path_id_seq'),primary_key=True),
    Column('cfg_tld_id', Integer, ForeignKey('cfg_tld.id'), nullable=False),
    Column('relative_path', String(64), index=True, nullable=False),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('last_used', DateTime, default=datetime.datetime.now),
    Column('comments',String(255),nullable=True))
#TODO: unique tld/relative_path
cfg_path.create(checkfirst=True)

class CfgPath(aqdbBase):
    """ Config path is a path which must fit into one of the predefined
        categories laid out in cfg_tld. Those higher level constructs need
        to be at the top of the path.(hardware, service, etc.)

        The individual config paths are created against this base class.
    """
    @optional_comments
    def __init__(self,pth):
        if isinstance(pth,str):
            pth = pth.lstrip('/').lower()
            try:
                tld=Session.query(CfgTLD).filter_by(type=splitall(pth)[0]).one()
            except NoSuchRowException:
                print "Can't find top level element '%s'"
            else:
                self.relative_path = '/'.join(splitall(pth)[1:])
                self.tld=tld
        else:
            raise TypeError('path must be a string')
            return
    def __str__(self):
        return '%s/%s'%(self.tld,self.relative_path)
    def __repr__(self):
        return '%s/%s'%(self.tld,self.relative_path)

mapper(CfgPath,cfg_path,properties={
    'tld': relation(CfgTLD,remote_side=cfg_tld.c.id,lazy=False),
    'category':relation(CfgTLD,remote_side=cfg_tld.c.type),
    'creation_date':deferred(cfg_path.c.creation_date),
    'comments':deferred(cfg_path.c.comments)})

domain = Table('domain', meta,
    Column('id', Integer, Sequence('domain_id_seq'), primary_key=True),
    Column('name', String(32), unique=True, index=True),
    #TODO: a better place for dns-domain. We'll need to flesh out DNS support
    #within aqdb in the coming weeks after the handoff, but for now,
    #it's an innocuous place since hosts can only be in one domain
    Column('dns_domain_id', Integer,
           ForeignKey('dns_domain.id'), nullable=False, default=2),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
domain.create(checkfirst=True)

class Domain(aqdbBase):
    """ Domain is to be used as the top most level for path traversal of the SCM
            Represents individual config repositories
    """
mapper(Domain,domain,properties={
    'dns_domain': relation(DnsDomain),
    'creation_date':deferred(domain.c.creation_date),
    'comments':deferred(domain.c.comments)})

"""
    The service list table is used to represent the service requirements of
    host 'build archetypes'. It groups required services into groupings that
    can be referenced and reused at build time. The list object is here
    because archteype requires is as a parent. Service list 'item' requires
    Service as a parent, and is included there instead.
"""
service_list = Table('service_list', meta,
    Column('id', Integer, Sequence('service_list_id_seq'), primary_key=True),
    Column('name', String(32), unique=True, index=True),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
service_list.create(checkfirst=True)


class ServiceList(aqdbBase):
    """ A bucket to put required services into as a list of required
        service dependencies for hosts.
    """
    pass
mapper(ServiceList,service_list,properties={
    'creation_date' : deferred(service_list.c.creation_date),
    'comments': deferred(service_list.c.comments)})

archetype = Table('archetype', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(32), unique=True, nullable=True, index=True),
    Column('service_list_id', Integer,
           ForeignKey('service_list.id',
                      ondelete='RESTRICT',
                      onupdate='CASCADE'),
           nullable=False),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
archetype.create(checkfirst=True)

class Archetype(aqdbBase):
    """Describes high level template requirements for building hosts """
    @optional_comments
    def __init__(self,name,**kw):
        if isinstance(name,str):
            self.name=name.strip().lower()
        #just look for archetype/name/base.tpl and final for now
            s=Session()
            try:
                self.first = s.query(CfgPath).filter_by(
                    relative_path='%s/base.tpl'%(self.name)).one()
            except NoSuchRowException:
                print "Can't find archetype/%s/base.tpl"%(self.name)
                return
            try:
                self.last=s.query(CfgPath).filter_by(
                    relative_path='%s/final.tpl'%(self.name)).one()
            except NoSuchRowException:
                print "Can't find archetype/%s/final.tpl"%(self.name)
                return
            try:
                self.service_list=s.query(
                    ServiceList).filter_by(name=self.name).one()
            except NoSuchRowException:
                print "Can't find a service list for %s"%(self.name)
                return
mapper(Archetype,archetype, properties={
    'service_list':relation(ServiceList, backref='archetype'),
    'creation_date' : deferred(archetype.c.creation_date),
    'comments': deferred(archetype.c.comments)
})

#######POPULATION FUNCTIONS########
def populate_tld():
    if empty(cfg_tld, engine):
        import os
        tlds=[]
        for i in os.listdir(const.cfg_base):
            if os.path.isdir(os.path.abspath(
                os.path.join(const.cfg_base,i ))) :
                    tlds.append(i)

        fill_type_table(cfg_tld, tlds)

def populate_cst():
    if empty(cfg_source_type,engine):
        fill_type_table(cfg_source_type,['quattor','aqdb'])

def create_paths():
    if empty(cfg_path,engine):
        from aquilon.aqdb.utils import altpath
        d=altpath.path(const.cfg_base)
        for file in d.walk('*.tpl'):
            (a,b,c)=file.partition('template-king/')
            try:
                #print c
                f=CfgPath(c)
                Session.save(f)
            except Exception,e:
                print e
                Session.rollback()
                continue
        Session.commit()
        print 'created configuration paths'

def create_domains():
    if empty(domain,engine):
        s=Session()

        p = Domain('production',comments='The master production area')
        q = Domain('qa',comments='Do your testing here')
        s.save(p)
        s.save(q)
        s.commit()
        print 'created production and qa domains'

def create_aquilon_archetype():
    if empty(archetype, engine):
        a=Archetype('aquilon')
        Session.save(a)
        Session.commit()

def get_quattor_src():
    """ ugly ugly way to initialize a quattor repo for import"""

    import os
    import exceptions
    if os.path.exists(const.cfg_base):
        return

    remote_dir = 'blackcomb:/var/tmp/daqscott/quattor/*'
    try:
        os.makedirs(const.cfg_base)
    except exceptions.OSError, e:
        pass
    print 'run "scp -r %s %s in a seperate window."'%(remote_dir,const.cfg_base)
    raw_input("When you've completed this, press any key")



if __name__ == '__main__':
    get_quattor_src()
    populate_tld()
    populate_cst()
    create_paths()
    create_domains()
    create_aquilon_archetype()

    s=Session()

    a=s.query(CfgTLD).first()
    b=s.query(CfgSourceType).first()
    c=s.query(CfgPath).first()
    d=s.query(Domain).first()
    e=s.query(Archetype).first()

    assert(a)
    assert(b)
    assert(c)
    assert(d)
    assert(e)


#TODO: this key/value attribute of aqdb config source
#TODO: figure out quattor config source
#TODO: svc_cfg_source: tell services are configured by quattor or aqdb?
"""
def create_qcs():
    if empty(quattor_cfg_source,engine):
        s=Session()

        prod=s.query(Domain).filter_by(name='production').one()
        for i in s.query(CfgPath).all():
            qcs = QuattorCfgSource(prod,i)
            s.save(qcs)
            s.commit()
"""
