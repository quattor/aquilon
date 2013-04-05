# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2011,2012,2013  Contributor
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

from sqlalchemy import Integer, Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.model import Resource, Machine

_TN = 'virtual_machine'


class VirtualMachine(Resource):
    """ Virtual machine resources """
    __tablename__ = _TN
    _class_label = 'Virtual Machine'

    resource_id = Column(Integer, ForeignKey('resource.id',
                                             name='%s_resource_fk' % _TN,
                                             ondelete='CASCADE'),
                         primary_key=True)

    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                            name='%s_machine_fk' % _TN,
                                            ondelete='CASCADE'),
                        nullable=False)

    machine = relation(Machine, innerjoin=True,
                       backref=backref('vm_container', uselist=False,
                                       cascade='all'))

    # A machine can be assigned to one holder only.
    __table_args__ = (UniqueConstraint(machine_id,
                                       name='%s_machine_uk' % _TN),)
    __mapper_args__ = {'polymorphic_identity': 'virtual_machine'}

vm = VirtualMachine.__table__
vm.primary_key.name = '%s_pk' % _TN
vm.info['unique_fields'] = ['name', 'holder']
