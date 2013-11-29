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
""" basic construct of model = vendor name + product name """

from datetime import datetime

from sqlalchemy import (Integer, DateTime, Sequence, String, Column, ForeignKey,
                        UniqueConstraint)

from sqlalchemy.orm import relation, object_session, deferred

from aquilon.exceptions_ import AquilonError
from aquilon.aqdb.model import Base, Vendor
from aquilon.aqdb.column_types import AqStr, StringEnumColumn

from aquilon.aqdb.types import ModelType, NicType


class Model(Base):
    """ Vendor and Model are representations of the various manufacturers and
    the asset inventory of the kinds of machines we use in the plant """
    __tablename__ = 'model'

    id = Column(Integer, Sequence('model_id_seq'), primary_key=True)
    name = Column(AqStr(64), nullable=False)

    vendor_id = Column(Integer, ForeignKey('vendor.id',
                                           name='model_vendor_fk'),
                       nullable=False)

    model_type = Column(StringEnumColumn(ModelType, 20, True), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = Column(String(255))

    vendor = relation(Vendor, innerjoin=True)

    __table_args__ = (UniqueConstraint(vendor_id, name,
                                       name='model_vendor_name_uk'),)

    def __format__(self, format_spec):
        instance = "%s/%s" % (self.vendor.name, self.name)
        return self.format_helper(format_spec, instance)

    @classmethod
    def default_nic_model(cls, session):
        # TODO: make this configurable
        return cls.get_unique(session, model_type=NicType.Nic, name='generic_nic',
                              vendor='generic', compel=AquilonError)

    @property
    def nic_model(self):
        if self.machine_specs:
            return self.machine_specs.nic_model

        session = object_session(self)
        return self.default_nic_model(session)

model = Model.__table__  # pylint: disable=C0103
model.info['unique_fields'] = ['name', 'vendor']
model.info['extra_search_fields'] = ['model_type']
