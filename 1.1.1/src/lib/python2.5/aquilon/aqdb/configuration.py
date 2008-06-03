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
from subtypes import subtype
from name_table import make_name_class
from aquilon import const

from sqlalchemy import Table, Integer, Sequence, String, ForeignKey, Index
from sqlalchemy.orm import mapper, relation, deferred

import os
const.cfg_base = config.get("broker", "kingdir")

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

tl_doc = """ Configuration Top Level Directory or 'cfg_tld' are really the high level
        namespace categories, or the directories in /var/quattor/template-king
            base      (only one for now)
            os        (major types (linux,solaris) prefabricated)
            hardware  entered by model (vendors + types prefabricated)
            services
            feature  also need groups
            final     (only one for now)
            personality is really just app (or service if its consumable too)
    """
CfgTLD= subtype('CfgTLD','cfg_tld',tl_doc)
cfg_tld = CfgTLD.__table__
cfg_tld.create(checkfirst=True)


cfg_path = Table('cfg_path',meta,
    Column('id', Integer, Sequence('cfg_path_id_seq'), primary_key=True),
    Column('cfg_tld_id', Integer, ForeignKey('cfg_tld.id'), nullable=False),
    Column('relative_path', String(255), index=True, nullable=False),
    Column('creation_date', DateTime, default=datetime.now),
    Column('last_used', DateTime, default=datetime.now),
    Column('comments',String(255),nullable=True),
    UniqueConstraint('cfg_tld_id','relative_path',name='cfg_path_uk'))
Index('cfg_relative_path_idx', cfg_path.c.relative_path)
cfg_path.create(checkfirst=True)

class CfgPath(aqdbBase):
    """ Config path is a path which must fit into one of the predefined
        categories laid out in cfg_tld. Those higher level constructs need
        to be at the top of the path.(hardware, service, etc.)

        The individual config paths are created against this base class.
    """
    @optional_comments
    def __init__(self, tld, pth):
        if isinstance(tld, CfgTLD):
            self.tld = tld
        else:
            raise ArgumentError("First argument must be a CfgTLD")

        if isinstance(pth,str):
            pth = pth.lstrip('/').lower()
            self.relative_path = '/'.join(splitall(pth)[1:])
        else:
            raise TypeError('path must be a string')
            return
    def __str__(self):
        return '%s/%s'%(self.tld,self.relative_path)
    def __repr__(self):
        return '%s/%s'%(self.tld,self.relative_path)

mapper(CfgPath,cfg_path,properties={
    'tld': relation(CfgTLD,remote_side=cfg_tld.c.id,lazy=False),
    'creation_date':deferred(cfg_path.c.creation_date),
    'comments':deferred(cfg_path.c.comments)})

Archetype = make_name_class('Archetype','archetype')
archetype = Archetype.__table__
archetype.create(checkfirst=True)


#######POPULATION FUNCTIONS########
def populate_tld():
    if empty(cfg_tld):
        import os
        tlds=[]
        for i in os.listdir(const.cfg_base):
            p = os.path.abspath(os.path.join(const.cfg_base, i))
            if os.path.isdir(p):
                # Hack to consider all subdirectories of the archetype
                # as a tld.
                if i == "aquilon":
                    for j in os.listdir(p):
                        if os.path.isdir(os.path.abspath(os.path.join(p, j))):
                            tlds.append(j)
                elif i == ".git":
                    continue
                else:
                    tlds.append(i)

        print "Adding these CfgTLDs: ", str(tlds)
        fill_type_table(cfg_tld, tlds)

def create_paths():
    s = Session()
    if empty(cfg_path):
        for root, dirs, files in os.walk(const.cfg_base):
            if ".git" in dirs:
                dirs.remove(".git")
            if root == const.cfg_base:
                continue
            tail = root.replace(const.cfg_base + "/", "", 1)
            # Treat everything under aquilon as equivalent to a tld.
            # It might be better to have an archetype attribute on
            # the cfgpath...
            if tail == "aquilon":
                continue
            if tail.startswith("aquilon/"):
                tail = tail.replace("aquilon/", "", 1)
            slash = tail.find("/")
            if slash < 0:
                continue
            tld = tail[0:slash]
            try:
                dbtld = s.query(CfgTLD).filter_by(type=tld).one()
                f = CfgPath(dbtld, tail)
                s.save_or_update(f)
            except Exception, e:
                print e
                s.rollback()
                continue
        s.commit()
        print 'created configuration paths'

def create_aquilon_archetype():
    s = Session()
    if empty(archetype):
        a=Archetype(name='aquilon',comments='AutoPopulated')
        s.save(a)
        s.commit()
        print 'created aquilon archetype'
    s.close()

if __name__ == '__main__':
    populate_tld()
    create_paths()
    create_aquilon_archetype()

    s=Session()

    a=s.query(CfgTLD).first()
    b=s.query(CfgPath).first()
    c=s.query(Archetype).first()

    assert(a)
    assert(b)
    assert(c)
