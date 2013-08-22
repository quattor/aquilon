# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime

from sqlalchemy import (Column, Enum, Integer, DateTime, Sequence,
                        String, UniqueConstraint, event)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import deferred
from sqlalchemy.orm.session import object_session

from aquilon.config import Config
from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Base, StateEngine, HostLifecycle
from aquilon.aqdb.column_types import Enum

_TN = 'clusterlifecycle'


class ClusterLifecycle(StateEngine, Base):
    """ Describes the state a cluster is within the provisioning lifecycle """

    transitions = {'build': ['ready', 'decommissioned'],
                   'ready': ['rebuild', 'decommissioned'],
                   'rebuild': ['ready', 'decommissioned'],
                   'decommissioned': ['rebuild']}

    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    name = Column(Enum(32, transitions.keys()), nullable=False)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    __table_args__ = (UniqueConstraint(name, name='%s_uk' % _TN),)
    __mapper_args__ = {'polymorphic_on': name}

    def __repr__(self):
        return str(self.name)

clusterlifecycle = ClusterLifecycle.__table__  # pylint: disable=C0103
clusterlifecycle.info['unique_fields'] = ['name']

event.listen(clusterlifecycle, "after_create",
             ClusterLifecycle.populate_const_table)


"""
The following classes are the actual lifecycle states for a cluster.

WARNING: The classes Decommissioned, Ready, Rebuild and Build have the same name
as 4 classes in hostlifecycle and have odd behaviors when imported into the same
namespace. It would be ill advised to do use these clashing clasess in the
same module.

Perhaps it's best to illustrate by example:

from aquilon.aqdb.model.clusterlifecycle import Ready

session.query(Ready).first()
    Out[31]: ready
type(r)
    Out[32]: <class 'aquilon.aqdb.model.clusterlifecycle.Ready'>

from aquilon.aqdb.model.hostlifecycle import Ready
r=s.query(Ready).first()
type(r)
    Out[35]: <class 'aquilon.aqdb.model.hostlifecycle.Ready'>

from aquilon.aqdb.model.clusterlifecycle import Ready
r=s.query(Ready).first()
type(r)
    Out[55]: <class 'aquilon.aqdb.model.clusterlifecycle.Ready'>
"""


class Decommissioned(ClusterLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'decommissioned'}

    # can't set the status to "decommissioned" if the cluster has VMs.
    def onEnter(self, dbcluster):
        dbdecommissioned = HostLifecycle.get_unique(object_session(dbcluster),
                                                    "decommissioned",
                                                    compel=True)

        config = Config()
        archetype = dbcluster.personality.archetype
        section = "archetype_" + archetype.name
        opt = "allow_cascaded_deco"

        if dbcluster.hosts and (not config.has_option(section, opt) or
                                not config.getboolean(section, opt)):
            raise ArgumentError("Cannot change state to {0}, as {1}'s "
                                "archetype is {2}."
                                .format(dbdecommissioned.name, dbcluster,
                                        archetype.name))

        if dbcluster.virtual_machines:
            raise ArgumentError("Cannot change state to {0}, as {1} has "
                                "{2} VM(s)."
                                .format(dbdecommissioned.name, dbcluster,
                                        len(dbcluster.virtual_machines)))

        for dbhost in dbcluster.hosts:
            dbhost.status.transition(dbhost, dbdecommissioned)


class Ready(ClusterLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'ready'}

    def onEnter(self, dbcluster):
        dbready = HostLifecycle.get_unique(object_session(dbcluster),
                                           "ready", compel=True)
        for dbhost in dbcluster.hosts:
            if dbhost.status.name == 'almostready':
                dbhost.status.transition(dbhost, dbready)

    def onLeave(self, dbcluster):
        dbalmostready = HostLifecycle.get_unique(object_session(dbcluster),
                                                 "almostready", compel=True)
        for dbhost in dbcluster.hosts:
            if dbhost.status.name == 'ready':
                dbhost.status.transition(dbhost, dbalmostready)


class Rebuild(ClusterLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'rebuild'}


class Build(ClusterLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'build'}
