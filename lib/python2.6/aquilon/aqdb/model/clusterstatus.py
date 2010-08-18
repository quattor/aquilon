# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
                        String, ForeignKey, UniqueConstraint)

from aquilon.aqdb.model import Base
from aquilon.utils import monkeypatch
from aquilon.aqdb.column_types import Enum
from aquilon.exceptions_ import ArgumentError


''' 
This stateful view describes where the cluster is within it's
provisioning lifecycle. 
'''
_TN = 'clusterlifecycle'
class ClusterLifecycle(Base):
    transitions = {
               'build'        : ['ready', 'decomissioned'],
               'ready'        : ['decommissioned'],
               'decommissioned' : [],
               }

    __tablename__ = _TN
    id = Column(Integer, Sequence('%s_id_seq'%(_TN)), primary_key=True)
    name = Column(Enum(32, transitions.keys()), nullable=False)
    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)
    __mapper_args__ = { 'polymorphic_on': name }

    def __repr__(self):
        return str(self.name)

    def transition(self, session, obj, to):
        '''Transition to another state. 

        session -- the sqlalchemy session
        host -- the object which wants to change state
        to -- the target state name

        returns a new state object for the target state, or
        throws an ArgumentError exception if the state cannot
        be reached. This method may be subclassed by states 
        if there is special logic regarding the transition.
        If the current state has an onLeave method, then the
        method will be called with the object as an argument.
        If the target state has an onEnter method, then the
        method will be called with the object as an argument.

        '''

        if to == self.name:
            return self

        if to not in ClusterLifecycle.transitions:
            raise ArgumentError("status of %s is invalid" % to)

        targets = ClusterLifecycle.transitions[self.name]
        if to not in targets:
            raise ArgumentError(("cannot change state to %s from %s. " +
                   "Legal states are: %s") % (to, self.name,
                   ", ".join(targets)))

        ret = ClusterLifecycle.get_unique(session, to, compel=True)
        if hasattr(self, 'onLeave'):
            self.onLeave(obj)
        obj.status = ret
        if hasattr(ret, 'onEnter'):
            ret = ret.onEnter(obj)
        return ret

clusterlifecycle = ClusterLifecycle.__table__
clusterlifecycle.primary_key.name='%s_pk'%(_TN)
clusterlifecycle.append_constraint(UniqueConstraint('name',name='%s_uk'%(_TN)))
clusterlifecycle.info['unique_fields'] = ['name']

@monkeypatch(clusterlifecycle)
def populate(sess, *args, **kw):
    from sqlalchemy.exceptions import IntegrityError

    statuslist = ClusterLifecycle.transitions.keys()

    i = clusterlifecycle.insert()
    for name in statuslist:
        try:
            i.execute(name=name)
        except IntegrityError:
            pass

    assert len(sess.query(ClusterLifecycle).all()) == len(statuslist)


'''
The following classes are the actual lifecycle states for a cluster
'''

class Decommissioned(ClusterLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'decommissioned'}
    pass


class Ready(ClusterLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'ready'}

    def onEnter(self, host):
        for dbhost in dbcluster.hosts:
            if dbhost.status.name == 'almostready':
                logger.info("promoting %s from almostready to ready" % 
                            dbhost.fqdn)
                dbhost.status = dbhost.status.transition(dbhost, 'ready')
                session.add(dbhost)

        return self


class Build(ClusterLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'build'}
    pass

