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

from datetime import datetime

from sqlalchemy import Column, Enum, Integer, DateTime, Sequence, event
from sqlalchemy.orm import object_session, deferred

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import LifecycleEngine, Base
from aquilon.aqdb.column_types import Enum

_TN = 'asset_lifecycle'


class AssetLifecycle(LifecycleEngine, Base):
    """ Describes the state a asset is within the provisioning lifecycle """

    transitions = {'evaluation': ['pre_prod', 'withdrawn'],
                   'pre_prod': ['withdrawn', 'early_prod'],
                   'early_prod': ['withdrawn', 'production'],
                   'production': ['inactive', 'pre_decommission'],
                   'pre_decommission': ['inactive'],
                   'inactive': ['decommissioned'],
                   'withdrawn': [],
                   'decommissioned': []
                  }

    __tablename__ = _TN
    _class_label = 'Asset Lifecycle'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    name = Column(Enum(32, list(transitions.keys())), nullable=False, unique=True)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    __table_args__ = ({'info': {'unique_fields': ['name']}},)
    __mapper_args__ = {'polymorphic_on': name}

    def __repr__(self):
        return str(self.name)

assetlifecycle = AssetLifecycle.__table__  # pylint: disable=C0103
event.listen(assetlifecycle, "after_create", AssetLifecycle.populate_const_table)


class Evaluation(AssetLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'evaluation'}


class Decommissioned(AssetLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'decommissioned'}


class PreProd(AssetLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'pre_prod'}


class EarlyProd(AssetLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'early_prod'}


class Production(AssetLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'production'}


class PreDecommission(AssetLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'pre_decommission'}


class Inactive(AssetLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'inactive'}


class Withdrawn(AssetLifecycle):
    __mapper_args__ = {'polymorphic_identity': 'withdrawn'}
