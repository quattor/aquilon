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

from sys import path, exit
#path.append('./utils')
if __name__ == '__main__':
    path.append('../..')

from DB import meta, engine, Session, aqdbBase, aqdbType
from aquilon.aqdb.utils.debug import ipshell
from aquilon.aqdb.utils.schemahelpers import *

s=Session()

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
    Column('path', String(64), index=True),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments',String(255)),
    UniqueConstraint('cfg_tld_id','path'))

cfg_path.create(checkfirst=True)

class CfgPath(aqdbBase):
    """ Config path is a path which must fit into one of the predefined
        categories laid out in cfg_tld. Those higher level constructs need
        to be at the top of the path.(hardware, service, etc.)

        The individual config paths are created against this base class.
    """
    def __init__(self,path):
        #do tld detection with errors
        #path.split('/')[1]
        if isinstance(path,str):
            self.path = path
        else:
            raise TypeError('path must be a string')
            return
    def __repr__(self):
        return '%s/%s'%(self.cfg_tld,self.path,)

mapper(CfgPath,cfg_path,properties={
    'tld': relation(CfgTLD,lazy=False),
    'creation_date':deferred(cfg_path.c.creation_date),
    'comments':deferred(cfg_path.c.comments)})

domain = mk_name_id_table('domain', meta, Column('comments',String(255)))
domain.create(checkfirst=True)

class Domain(aqdbBase):
    """ Domain is to be used as the top most level for path traversal of the SCM
            Represents individual config repositories
    """
mapper(Domain,domain,properties={
    'creation_date':deferred(domain.c.creation_date),
    'comments':deferred(domain.c.comments)})

#Quattor Source: path + domain (+quattor system?)

#######POPULATION FUNCTIONS########
def populate_tld():
    if empty(cfg_tld, engine):
        fill_type_table(cfg_tld,
                    ['base', 'hardware', 'os', 'service', 'feature', 'final',
                     'personality'])

def populate_cst():
    if empty(cfg_source_type,engine):
        fill_type_table(cfg_source_type,['quattor','aqdb'])

def create_paths():
    if empty(cfg_path,engine):
        a=CfgPath('base/aquilon')
        b=CfgPath('service/afs/q.ny.ms.com/client/config')
        c=CfgPath('personality/grid/server/config')
        d=CfgPath('os/linux/4.0.1-x86_64/config')
        e=CfgPath('hardware/ibm/hs20/config')
        f=CfgPath('final/config')

        for i in [a,b,c,d,e,f]:
            s.save(i)
        s.commit()
def create_domains():
    if empty(domain,engine):
        p = Domain('production',comments='The master production area')
        q = Domain('qa',comments='Do your testing here')
        s.save(p)
        s.save(q)
        s.commit()

def create_qcs():
    if empty(quattor_cfg_source,engine):
        prod=s.query(Domain).filter_by(name='production').one()
        for i in s.query(CfgPath).all():
            qcs = QuattorCfgSource(prod,i)
            s.save(qcs)
            s.commit()

if __name__ == '__main__':
    populate_tld()
    populate_cst()
    create_paths()
    create_domains()
    #create_qcs()

    s=Session()
    a=s.query(CfgTLD).first()

    b=s.query(CfgSourceType).first()
    ipshell()
    exit(0)

#TODO: this key/value thingy

### When you're done with the above, break from this, complete hardware, then
# and define the hardware config source in that module, and put host there.
# work with hardware for a while, and make sure the config path elements are
# the way you want them.

#TODO: svc_cfg_source: tell services are configured by quattor or aqdb?
