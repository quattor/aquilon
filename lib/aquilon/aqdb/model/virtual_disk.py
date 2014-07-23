# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
""" Disk for share """

import re

from sqlalchemy import Column, Boolean, Integer, ForeignKey, Index
from sqlalchemy.orm import relation, column_property, validates
from sqlalchemy.sql import select, func

from aquilon.aqdb.model import Disk, Resource, Share, Filesystem

_TN = 'disk'


class VirtualDisk(Disk):
    _address_re = re.compile(r"\d+:\d+$")

    snapshotable = Column(Boolean(name="%s_snapshotable_ck" % _TN),
                          nullable=True)

    backing_store_id = Column(Integer, ForeignKey(Resource.id,
                                                  name='%s_backing_store_fk' % _TN),
                              nullable=True)

    backing_store = relation(Resource)

    __mapper_args__ = {'polymorphic_identity': 'virtual_disk'}
    __extra_table_args__ = (Index('%s_backing_store_idx' % _TN, backing_store_id),)

    def __init__(self, address=None, backing_store=None, **kw):
        if not address:
            raise ValueError("Address is mandatory for virtual disks.")
        if not backing_store:
            raise ValueError("Backing store is mandatory for virtual disks.")
        super(VirtualDisk, self).__init__(address=address,
                                          backing_store=backing_store, **kw)

    def __repr__(self):
        return "<%s %s (%s) of machine %s, %d GB, stored on %s of %s>" % \
            (self._get_class_label(), self.device_name,
             self.controller_type, self.machine.label, self.capacity,
             format(self.backing_store),
             format(self.backing_store.holder.toplevel_holder_object))

    @validates("backing_store")
    def validate_backing_store(self, key, value):  # pylint: disable=W0613
        if not isinstance(value, Share) and \
           not isinstance(value, Filesystem):
            raise ValueError("The backing store must be a Share or Filesystem.")
        return value

# The formatter code is interested in the count of disks/machines, and it is
# cheaper to query the DB than to load all entities into memory
Share.virtual_disk_count = column_property(
    select([func.count()],
           VirtualDisk.backing_store_id == Share.id)
    .label("virtual_disk_count"), deferred=True)

Share.virtual_machine_count = column_property(
    select([func.count(func.distinct(VirtualDisk.machine_id))],
           VirtualDisk.backing_store_id == Share.id)
    .label("virtual_machine_count"), deferred=True)

Filesystem.virtual_disk_count = column_property(
    select([func.count()],
           VirtualDisk.backing_store_id == Filesystem.id)
    .label("virtual_disk_count"), deferred=True)
