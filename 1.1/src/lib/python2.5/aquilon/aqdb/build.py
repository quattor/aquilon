#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Left in its own module as it depends on many of the others to exist
    first to avoid circular dependencies """
import datetime

import sys
sys.path.append('../..')

from db import *
from service import Host
from configuration import CfgPath
from aquilon.aqdb.utils.schemahelpers import *

from sqlalchemy import Column, Integer, Sequence, String, ForeignKey
from sqlalchemy.orm import mapper, relation, deferred

host     = Table('host', meta, autoload=True)
cfg_path = Table('cfg_path', meta, autoload=True)


build = Table('build', meta,
    Column('id', Integer, primary_key=True),
    Column('host_id', Integer,
           ForeignKey('host.id'), unique=True, nullable=False, index=True),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
build.create(checkfirst=True)

class Build(aqdbBase):
    """ Identifies the build process of a given Host.
        Parent of 'build_element' """
    def __init__(self,host):
        if isinstance(host,Host):
            self.host=host
        else:
            msg = 'Build object requires a Host object for its constructor'
            raise ArgumentError()
    def __repr__(self):
        return 'Build Information for %s'%(self.host.name)

mapper(Build,build,properties={
    'creation_date' : deferred(build.c.creation_date),
    'comments': deferred(build.c.comments)
})

build_element = Table('build_element', meta,
    Column('id',Integer, primary_key=True),
    Column('build_id', Integer,
           ForeignKey('build.id',
                      ondelete='CASCADE',
                      onupdate='CASCADE'),
           nullable=False,
           index=True),
    Column('cfg_path_id', Integer,
           ForeignKey('cfg_path.id',
                      ondelete='RESTRICT',
                      onupdate='CASCADE'),
           nullable=False),
    Column('order', Integer, nullable=False),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
build_element.create(checkfirst=True)

class BuildElement(aqdbBase):
    pass
mapper(BuildElement,build_element, properties={
    'build'         : relation(BuildElement),
    'cfg_path'      : relation(CfgPath),
    'creation_date' : deferred(build_element.c.creation_date),
    'comments'      : deferred(build_element.c.comments)
})
#unique on host,cfg_path
#unique on build_id/order
#primary key should be host_id/order
#somewhere in this or chost, a change should trigger an
#update_time column on some table to update


if __name__ == '__main__':
    from aquilon.aqdb.utils.debug import ipshell
    ipshell()
