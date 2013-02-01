# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.

from datetime import datetime

from sqlalchemy import (Column, Enum, Integer, DateTime, Sequence,
                        String, UniqueConstraint)
from sqlalchemy.orm import deferred
from sqlalchemy.orm.session import object_session

from aquilon.config import Config
from aquilon.aqdb.model import Base, StateEngine, HostLifecycle
from aquilon.utils import monkeypatch
from aquilon.aqdb.column_types import Enum
from aquilon.exceptions_ import ArgumentError

_TN = 'clusterlifecycle'


class ClusterLifecycle(StateEngine, Base):
    """ Describes the state a cluster is within the provisioning lifecycle """

    transitions = {
               'build'        : ['ready', 'decommissioned'],
               'ready'        : ['rebuild', 'decommissioned'],
               'rebuild'      : ['ready', 'decommissioned'],
               'decommissioned' : ['rebuild'],
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


clusterlifecycle = ClusterLifecycle.__table__  # pylint: disable=C0103
clusterlifecycle.primary_key.name = '%s_pk' % _TN
clusterlifecycle.append_constraint(UniqueConstraint('name', name='%s_uk' % _TN))
clusterlifecycle.info['unique_fields'] = ['name']


@monkeypatch(clusterlifecycle)
def populate(sess, *args, **kw):  # pragma: no cover
    from sqlalchemy.exc import IntegrityError

    statuslist = ClusterLifecycle.transitions.keys()

    i = clusterlifecycle.insert()
    for name in statuslist:
        try:
            i.execute(name=name)
        except IntegrityError:
            pass

    assert len(sess.query(ClusterLifecycle).all()) == len(statuslist)


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
        opt = "%s_allow_cascaded_deco" % archetype.name

        if dbcluster.hosts and (not config.has_option("broker", opt) or
                                not config.getboolean("broker", opt)):
            raise ArgumentError("Cannot change state to {0}, as {1}'s "
                                "archetype is {2}.".format(
                                                    dbdecommissioned.name,
                                                    dbcluster,
                                                    archetype.name))

        if dbcluster.machines:
            raise ArgumentError("Cannot change state to {0}, as {1} has "
                                "{2} VM(s).".format(
                                                    dbdecommissioned.name,
                                                    dbcluster,
                                                    len(dbcluster.machines)))

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
