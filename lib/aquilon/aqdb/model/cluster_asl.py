# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016  Contributor
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
""" Tables/classes for configuration of AutoStartList and SystemList
    attributes for clusters. """

from datetime import datetime
from sqlalchemy import (Column, DateTime, Integer, ForeignKey,
                        PrimaryKeyConstraint)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref, deferred, relation
from sqlalchemy.orm.collections import attribute_mapped_collection

from aquilon.exceptions_ import InternalError
from aquilon.aqdb.model import Resource, Base
from aquilon.aqdb.model.cluster import HostClusterMember

_TNPL = 'priority_list'
_TNMP = 'member_priority'


def _member_priority_creator(host, priority):
    for hcm in host.cluster._hosts:
        if hcm.host == host:
            return MemberPriority(member=hcm, priority=priority)

    # Should never happen
    raise InternalError("{0} is not a member of its cluster?".format(host))


class PriorityList(Resource):
    """ Table providing cluster-specific overrides for system priorities. """
    __tablename__ = _TNPL

    resource_id = Column(ForeignKey(Resource.id), primary_key=True)

    __table_args__ = ({'info': {'unique_fields': ['name', 'holder']}},)

    hosts = association_proxy("entries", "host",
                              creator=_member_priority_creator)


class MemberPriority(Base):
    __tablename__ = _TNMP

    priority_list_id = Column(ForeignKey(PriorityList.resource_id,
                                         ondelete="CASCADE"),
                              nullable=False)
    member_id = Column(ForeignKey(HostClusterMember.host_id,
                                  name="member_priority_member_fk",
                                  ondelete='CASCADE'),
                       nullable=False, index=True)
    priority = Column(Integer, nullable=False)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    __table_args__ = (PrimaryKeyConstraint(priority_list_id, member_id),)

    priority_list = relation(PriorityList,
                             backref=backref("entries",
                                             cascade="all, delete-orphan",
                                             collection_class=attribute_mapped_collection("host"),
                                             passive_deletes=True))
    member = relation(HostClusterMember, innerjoin=True)
    host = association_proxy("member", "host")


class SystemList(PriorityList):
    __mapper_args__ = {'polymorphic_identity': 'system_list'}


class AutoStartList(PriorityList):
    __mapper_args__ = {'polymorphic_identity': 'auto_start_list'}
