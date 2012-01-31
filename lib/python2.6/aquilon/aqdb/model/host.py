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
""" The majority of the things we're interested in for now are hosts. """

from datetime import datetime

from sqlalchemy import (Integer, Boolean, DateTime, String, Column, ForeignKey,
                        UniqueConstraint, Index)
from sqlalchemy.orm import relation, backref, deferred

from aquilon.aqdb.model import (Base, Branch, Machine, HostLifecycle, Grn,
                                Personality, OperatingSystem, UserPrincipal)

_TN = 'host'
_HOSTGRN = 'host_grn_map'


class Host(Base):
    """ The Host class captures the configuration profile of a machine.

        Putting a physical machine into a chassis and powering it up leaves it
        in a state with a few more attributes not filled in: what Branch
        configures this host? If Ownership is captured, this is the place for
        it.

        Post DNS changes the class name "Host", and it's current existence may
        not make much sense. In the interest of keeping the scope of changes
        somewhat limited (compared to how much else is changing), the class is
        being left in this intermediate state, for the time being. The full
        expression of the changes would be to call the class "MachineProfile",
        and remove any machine specific information. This would provide a more
        normalized schema, rather than individual machines having all of the
        rows below, which potentially would need to be nullable.
    """

    __tablename__ = _TN
    _instance_label = 'fqdn'

    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                            name='host_machine_fk'),
                        primary_key=True)

    branch_id = Column(Integer, ForeignKey('branch.id',
                                           name='host_branch_fk'),
                       nullable=False)

    sandbox_author_id = Column(Integer,
                               ForeignKey('user_principal.id',
                                          name='host_sandbox_author_fk'),
                               nullable=True)

    personality_id = Column(Integer, ForeignKey('personality.id',
                                                name='host_prsnlty_fk'),
                            nullable=False)

    lifecycle_id = Column(Integer, ForeignKey('hostlifecycle.id',
                                              name='host_lifecycle_fk'),
                          nullable=False)

    operating_system_id = Column(Integer, ForeignKey('operating_system.id',
                                                     name='host_os_fk'),
                                 nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = Column(String(255), nullable=True)

    # something to retain the advertised status of the host
    advertise_status = Column(Boolean(name="%s_advertise_status_valid_ck" % _TN),
                                      nullable=False, default=False)

    # Deletion of a machine deletes the host. When this is 'machine profile'
    # this should no longer be the case as it will be many to one as opposed to
    # one to one as it stands now.
    # This is a one-to-one relation, so we need uselist=False on the backref
    machine = relation(Machine, lazy=False, innerjoin=True,
                       backref=backref('host', uselist=False, lazy=False,
                                       cascade='all'))

    branch = relation(Branch, innerjoin=True, backref='hosts')
    sandbox_author = relation(UserPrincipal)
    personality = relation(Personality, innerjoin=True)
    status = relation(HostLifecycle, innerjoin=True)
    operating_system = relation(OperatingSystem, innerjoin=True)

    @property
    def fqdn(self):
        return self.machine.fqdn

    @property
    def archetype(self):
        """ proxy in our archetype attr """
        return self.personality.archetype

    @property
    def authored_branch(self):
        """ return a string representation of sandbox author/branch name """
        if self.sandbox_author:
            return "%s/%s" % (self.sandbox_author.name, self.branch.name)
        return str(self.branch.name)


host = Host.__table__  # pylint: disable=C0103, E1101
host.primary_key.name = 'host_pk'
host.append_constraint(
    UniqueConstraint('machine_id', 'branch_id', name='host_machine_branch_uk'))

Index('host_prsnlty_idx', host.c.personality_id)


class HostGrnMap(Base):
    __tablename__ = _HOSTGRN

    host_id = Column(Integer, ForeignKey("%s.machine_id" % _TN,
                                         name="%s_host_fk" % _HOSTGRN),
                     primary_key=True)

    eon_id = Column(Integer, ForeignKey('grn.eon_id',
                                        name='%s_grn_fk' % _HOSTGRN),
                    primary_key=True)

    host = relation(Host)
    grn = relation(Grn)


hostgrns = HostGrnMap.__table__  # pylint: disable=C0103, E1101
hostgrns.primary_key.name = "%s_pk" % _HOSTGRN

Host.grns = relation(Grn, secondary=HostGrnMap.__table__)
