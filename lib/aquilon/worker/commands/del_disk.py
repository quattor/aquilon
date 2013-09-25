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
"""Contains the logic for `aq del disk`."""

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import Disk, Machine
from aquilon.aqdb.model.disk import controller_types
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandDelDisk(BrokerCommand):

    required_parameters = ["machine"]

    def render(self, session, logger, machine, disk, controller, size, all,
               **arguments):
        dbmachine = Machine.get_unique(session, machine, compel=True)
        q = session.query(Disk).filter_by(machine=dbmachine)
        if disk:
            q = q.filter_by(device_name=disk)
        if controller:
            if controller not in controller_types:
                raise ArgumentError("%s is not a valid controller type, use "
                                    "one of: %s." % (controller,
                                                     ", ".join(controller_types)
                                                     ))
            q = q.filter_by(controller_type=controller)
        if size is not None:
            q = q.filter_by(capacity=size)
        results = q.all()

        if len(results) == 0:
            raise NotFoundException("No disks found.")
        elif len(results) > 1 and not all:
            raise ArgumentError("More than one matching disks found.  "
                                "Use --all to delete them all.")
        for result in results:
            session.delete(result)

        session.flush()
        session.expire(dbmachine, ['disks'])

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbmachine))
        dbcontainer = dbmachine.vm_container
        if dbcontainer:
            plenaries.append(Plenary.get_plenary(dbcontainer, logger=logger))

        plenaries.write()

        return
