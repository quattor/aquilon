# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2019  Contributor
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

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
)
from sqlalchemy.orm import (
    backref,
    relation,
)

from aquilon.aqdb.model import (
    Fqdn,
    Resource,
)

_TN = 'shared_sn'


class SharedServiceName(Resource):
    """Shared service name resources"""
    __tablename__ = _TN

    resource_id = Column(ForeignKey(Resource.id, ondelete='CASCADE',
                                    name='shared_sn_resource_id_fk'),
                         primary_key=True)

    # if true, indicates that address-aliases should be created from the FQDN
    # to particular service addresses in the same resourcegroup.
    sa_aliases = Column(Boolean, nullable=False)

    # FQDN is the 'shared service name' that is chosen -- must be a valid name
    # that the address-alias records can be created against
    fqdn_id = Column(ForeignKey(Fqdn.id), nullable=False, index=True)

    fqdn = relation(Fqdn, lazy=False, innerjoin=True,
                    backref=backref('shared_service_names'))

    __table_args__ = ({'info': {'unique_fields': ['name', 'holder']}},)

    __mapper_args__ = {'polymorphic_identity': _TN}
