#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""The tables/objects/mappings related to configuration in aquilon """

import datetime

import sys
if __name__ == '__main__':
    sys.path.append('../..')

from db import *

from aquilon.aqdb.utils.schemahelpers import *
from aquilon import const
from utils.exceptions_ import NoSuchRowException
from utils import altpath
const.cfg_base=altpath.path('/var/quattor/template-king/')

from sqlalchemy import *
from sqlalchemy.orm import *

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
    Column('cfg_tld_id', Integer, ForeignKey('cfg_tld.id')),
    Column('relative_path', String(64), index=True),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments',String(255)))

cfg_path.create(checkfirst=True)

class CfgPath(aqdbBase):
    """ Config path is a path which must fit into one of the predefined
        categories laid out in cfg_tld. Those higher level constructs need
        to be at the top of the path.(hardware, service, etc.)

        The individual config paths are created against this base class.
    """
    def __init__(self,pth):
        if isinstance(pth,str):
            pth = altpath.path(pth.lstrip('/').lower())
            try:
                tld=Session.query(CfgTLD).filter_by(type=pth[0]).one()
            except NoSuchRowException:
                print "Can't find top level element '%s'"
            else:
                self.relative_path = str(pth[1:])
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

domain = mk_name_id_table('domain', meta,)
#TODO: Column('host_id'), Integer, ForeignKey('host.id'), nullable=False)
domain.create(checkfirst=True)

class Domain(aqdbBase):
    """ Domain is to be used as the top most level for path traversal of the SCM
            Represents individual config repositories
    """
mapper(Domain,domain,properties={
    'creation_date':deferred(domain.c.creation_date),
    'comments':deferred(domain.c.comments)})

#Quattor Source: path + domain? Or, are paths to configurations fixed?

#######POPULATION FUNCTIONS########
def populate_tld():
    if empty(cfg_tld, engine):
        import os
        tlds=[]
        for i in os.listdir(str(const.cfg_base)):
            if os.path.isdir(os.path.abspath(
                os.path.join(str(const.cfg_base),i ))) :
                    tlds.append(i)

        fill_type_table(cfg_tld, tlds)

def populate_cst():
    if empty(cfg_source_type,engine):
        fill_type_table(cfg_source_type,['quattor','aqdb'])

def create_paths():
    if empty(cfg_path,engine):
        import os
        for root, dirs, files in os.walk(str(const.cfg_base)):
            if len(files) > 0:
                for i in files:
                    p = altpath.path(os.path.join(root,i))
                    print p[4:]
                    f=CfgPath(str(p[4:]))
                    Session.save(f)
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

if __name__ == '__main__':
    populate_tld()
    populate_cst()
    create_paths()
    create_domains()

    s=Session()

    a=s.query(CfgTLD).first()
    b=s.query(CfgSourceType).first()
    c=s.query(CfgPath).first()

    assert(a)
    assert(b)
    assert(c)

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
