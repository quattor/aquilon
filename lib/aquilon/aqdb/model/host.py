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
""" The majority of the things we're interested in for now are hosts. """

from datetime import datetime

from sqlalchemy import (Integer, Boolean, DateTime, String, Column, ForeignKey,
                        PrimaryKeyConstraint, Index)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relation, backref, deferred

from aquilon.aqdb.model import (Base, Branch, HardwareEntity, HostLifecycle, Grn,
                                Personality, OperatingSystem, UserPrincipal)

from aquilon.aqdb.column_types import AqStr
from collections import defaultdict

_TN = 'host'
_HOSTGRN = 'host_grn_map'


def _hgm_creator(tuple):
    return HostGrnMap(host=tuple[0], grn=tuple[1], target=tuple[2])


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

    hardware_entity_id = Column(Integer, ForeignKey('hardware_entity.id',
                                                    name='host_hwent_fk'),
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

    owner_eon_id = Column(Integer, ForeignKey('grn.eon_id',
                                              name='%s_owner_grn_fk' % _TN),
                          nullable=True)

    # something to retain the advertised status of the host
    advertise_status = Column(Boolean(name="%s_advertise_status_valid_ck" % _TN),
                              nullable=False, default=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = Column(String(255), nullable=True)

    # This is a one-to-one relation, so we need uselist=False on the backref
    hardware_entity = relation(HardwareEntity, lazy=False, innerjoin=True,
                               backref=backref('host', uselist=False,
                                               lazy=False,
                                               cascade='all, delete-orphan'))

    branch = relation(Branch, innerjoin=True, backref='hosts')
    sandbox_author = relation(UserPrincipal)
    personality = relation(Personality, innerjoin=True)
    status = relation(HostLifecycle, innerjoin=True)
    operating_system = relation(OperatingSystem, innerjoin=True)
    owner_grn = relation(Grn)
    grns = association_proxy('_grns', 'grn', creator=_hgm_creator)

    __table_args__ = (Index('host_prsnlty_idx', personality_id),
                      Index('%s_branch_idx' % _TN, branch_id))

    @property
    def fqdn(self):
        return self.hardware_entity.fqdn

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

    # see cluster.py
    @property
    def virtual_machines(self):
        mach = []
        if self.resholder:
            for res in self.resholder.resources:
                # TODO: support virtual machines inside resource groups?
                if res.resource_type == "virtual_machine":
                    mach.append(res.machine)
        return mach

    @property
    def effective_owner_grn(self):
        if self.owner_grn:
            return self.owner_grn
        else:
            return self.personality.owner_grn

    @property
    def effective_grns(self):
        ## process grns
        eon_id_map = defaultdict(set)
        pers_eon_id_map = defaultdict(set)

        # own
        for grn_rec in self._grns:
            eon_id_map[grn_rec.target].add(grn_rec.grn)
        for grn_rec in self.personality._grns:
            pers_eon_id_map[grn_rec.target].add(grn_rec.grn)

        for target in pers_eon_id_map:
            if target not in eon_id_map:
                eon_id_map[target] = pers_eon_id_map[target]

        return eon_id_map


class HostGrnMap(Base):
    __tablename__ = _HOSTGRN

    host_id = Column(Integer, ForeignKey("%s.hardware_entity_id" % _TN,
                                         name="%s_host_fk" % _HOSTGRN,
                                         ondelete="CASCADE"),
                     nullable=False)

    eon_id = Column(Integer, ForeignKey('grn.eon_id',
                                        name='%s_grn_fk' % _HOSTGRN),
                    nullable=False)

    host = relation(Host, innerjoin=True,
                    backref=backref('_grns', cascade='all, delete-orphan',
                                    passive_deletes=True))

    grn = relation(Grn, lazy=False, innerjoin=True,
                   backref=backref('_hosts', passive_deletes=True))

    target = Column(AqStr(32), nullable=False)

    __table_args__ = (PrimaryKeyConstraint(host_id, eon_id, target),)

    # used by unmap
    @property
    def mapped_object(self):
        return self.host
