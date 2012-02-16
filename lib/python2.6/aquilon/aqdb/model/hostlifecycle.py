# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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

from sqlalchemy.orm import object_session
from sqlalchemy import (Column, Enum, Integer, DateTime, Sequence, String,
                        UniqueConstraint)

from aquilon.aqdb.model import StateEngine, Base
from aquilon.utils import monkeypatch
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
               'decommissioned' : [],
               }

    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    name = Column(Enum(32, transitions.keys()), nullable=False)
    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    __mapper_args__ = {'polymorphic_on': name}

    def __repr__(self):
        return str(self.name)


hostlifecycle = HostLifecycle.__table__  # pylint: disable=C0103, E1101
hostlifecycle.primary_key.name = '%s_pk' % _TN
hostlifecycle.append_constraint(UniqueConstraint('name', name='%s_uk' % _TN))
hostlifecycle.info['unique_fields'] = ['name']


@monkeypatch(hostlifecycle)
def populate(sess, *args, **kw):  # pragma: no cover
    from sqlalchemy.exc import IntegrityError

    statuslist = HostLifecycle.transitions.keys()

    i = hostlifecycle.insert()
    for name in statuslist:
        try:
            i.execute(name=name)
        except IntegrityError:
            pass

    assert len(sess.query(HostLifecycle).all()) == len(statuslist)


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
