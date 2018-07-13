# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
""" Entitlements management """

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    Sequence,
    String,
)
from sqlalchemy.orm import (
    deferred,
    relation,
)

from aquilon.aqdb.column_types import AqStr
from aquilon.aqdb.model import (
    Base,
    UserType,
)
from aquilon.aqdb.utils.constraints import ref_constraint_name


_TYPES = 'entit_type'
_TYPESUSERMAP = 'entit_type_user_type_map'

_IDXSUFFIX = 'idx'


class EntitlementType(Base):
    __tablename__ = _TYPES

    id = Column(Integer, Sequence('%s_id_seq' % __tablename__),
                primary_key=True)
    name = Column(AqStr(64), nullable=False, unique=True)

    # Boolean to indicate if the entitlement type allows to set entitlement
    # to GRNs or not
    to_grn = Column(Boolean, nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = Column(String(255), nullable=True)

    __table_args__ = ({'info': {'unique_fields': ['name']}},)


class EntitlementTypeUserTypeMap(Base):
    __tablename__ = _TYPESUSERMAP

    entitlement_type_id = Column(ForeignKey(EntitlementType.id,
                                            ondelete='CASCADE'),
                                 nullable=False)
    entitlement_type = relation(EntitlementType, lazy=False, innerjoin=True)

    user_type_id = Column(ForeignKey(UserType.id, ondelete='CASCADE'),
                          nullable=False)
    user_type = relation(UserType, lazy=False, innerjoin=True)

    __table_args__ = (
        PrimaryKeyConstraint(entitlement_type_id, user_type_id),
        Index(ref_constraint_name(local_table=__tablename__,
                                  column='enttyp',
                                  suffix=_IDXSUFFIX),
              entitlement_type_id),
        Index(ref_constraint_name(local_table=__tablename__,
                                  column='usrtyp',
                                  suffix=_IDXSUFFIX),
              user_type_id),
    )


# List of user types an entitlement type allows to set entitlements to
EntitlementType.to_user_types = relation(EntitlementTypeUserTypeMap,
                                         cascade='all, delete-orphan',
                                         passive_deletes=True)
