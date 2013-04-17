# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

from sqlalchemy import (Column, Enum, Integer, DateTime, Sequence, String,
                        UniqueConstraint, event)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import object_session, deferred

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import StateEngine, Base
from aquilon.aqdb.column_types import Enum

_TN = 'hostlifecycle'


class HostLifecycle(StateEngine, Base):
    """ Describes the state a host is within the provisioning lifecycle """

    transitions = {
               'blind'        : ['build', 'failed', 'decommissioned'],
               'build'        : ['almostready', 'ready', 'failed',
                                 'rebuild', 'reinstall', 'decommissioned'],
               'install'      : ['build', 'reinstall', 'failed',
                                 'decommissioned'],
               'almostready'  : ['ready', 'rebuild', 'reinstall', 'failed',
                                 'decommissioned'],
               'ready'        : ['almostready', 'rebuild', 'reinstall',
                                 'failed', 'decommissioned'],
               'reinstall'    : ['rebuild', 'failed', 'decommissioned'],
               'rebuild'      : ['almostready', 'ready', 'reinstall', 'failed',
                                 'decommissioned'],
               'failed'       : ['rebuild', 'reinstall', 'decommissioned'],
               'decommissioned' : ['rebuild', 'reinstall'],
               }

    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    name = Column(Enum(32, transitions.keys()), nullable=False)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = Column(String(255), nullable=True)

    __mapper_args__ = {'polymorphic_on': name}

    def __repr__(self):
        return str(self.name)


hostlifecycle = HostLifecycle.__table__  # pylint: disable=C0103
hostlifecycle.primary_key.name = '%s_pk' % _TN
hostlifecycle.append_constraint(UniqueConstraint('name', name='%s_uk' % _TN))
hostlifecycle.info['unique_fields'] = ['name']

event.listen(hostlifecycle, "after_create", HostLifecycle.populate_const_table)


"""
The following classes are the actual lifecycle states for a host.

WARNING: The classes Decommissioned, Ready, Rebuild and Build have the same name
as 4 classes in clusterlifecycle and have odd behaviors when imported into the
same namespace. It would be ill advised to do use these clashing clasess in the
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


class Blind(HostLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'blind'}


class Decommissioned(HostLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'decommissioned'}

    def onEnter(self, obj):
        # can't set the status to "decommissioned" if the cluster has VMs.
        dbcluster = obj.cluster
        if dbcluster and dbcluster.status.name != "decommissioned":
            raise ArgumentError("Cannot change state to decommissioned, as "
                                "{0}'s state is not decommissioned.".format(dbcluster))


class Ready(HostLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'ready'}

    def onEnter(self, obj):
        if obj.cluster and obj.cluster.status.name != 'ready':
            dbstate = HostLifecycle.get_unique(object_session(obj),
                                               'almostready',
                                               compel=True)
            obj.status.transition(obj, dbstate)
        else:
            obj.advertise_status = True


class Almostready(HostLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'almostready'}


class Install(HostLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'install'}


class Build(HostLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'build'}


class Rebuild(HostLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'rebuild'}


class Reinstall(HostLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'reinstall'}


class Failed(HostLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'failed'}
