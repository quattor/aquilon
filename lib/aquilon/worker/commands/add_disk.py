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
"""Contains the logic for `aq add disk`."""

import re

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Machine, LocalDisk, VirtualDisk,
                                VirtualLocalDisk, Filesystem)
from aquilon.aqdb.model.disk import controller_types
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.resources import find_share
from aquilon.worker.templates import Plenary


class CommandAddDisk(BrokerCommand):
    """Add a disk object (local or share) to a machine"""
    # FIXME: add "controller" and "size" once the deprecated alternatives are
    # removed
    required_parameters = ["machine", "disk"]

    REGEX_ADDRESS = re.compile(r"\d+:\d+$")

    def render(self, session, logger, machine, disk, controller, share,
               filesystem, resourcegroup, address, comments, size, boot,
               snapshot, **kw):

        # Handle deprecated arguments
        if kw.get("type"):
            self.deprecated_option("type", "Please use --controller instead.",
                                   logger=logger, **kw)
            controller = kw["type"]
        if kw.get("capacity"):
            self.deprecated_option("capacity", "Please use --size instead.",
                                   logger=logger, **kw)
            size = kw["capacity"]
        if not size or not controller:
            raise ArgumentError("Please specify both --size "
                                "and --controller.")

        if controller not in controller_types:
            raise ArgumentError("%s is not a valid controller type, use one "
                                "of: %s." % (controller,
                                             ", ".join(controller_types)))

        dbmachine = Machine.get_unique(session, machine, compel=True)
        for dbdisk in dbmachine.disks:
            if dbdisk.device_name == disk:
                raise ArgumentError("Machine %s already has a disk named %s." %
                                    (machine, disk))
            if dbdisk.bootable:
                if boot is None:
                    boot = False
                elif boot:
                    raise ArgumentError("Machine %s already has a boot disk." %
                                        machine)

        if boot is None:
            # Backward compatibility: "sda"/"c0d0" is bootable, except if there
            # is already a boot disk
            boot = (disk == "sda" or disk == "c0d0")

        if share:
            if not CommandAddDisk.REGEX_ADDRESS.match(address):
                raise ArgumentError(r"Disk address '%s' is not valid, it must "
                                    r"match \d+:\d+ (e.g. 0:0)." % address)
            if not dbmachine.vm_container:
                raise ArgumentError("{0} is not a virtual machine, it is not "
                                    "possible to define a virtual disk."
                                    .format(dbmachine))

            dbshare = find_share(dbmachine.vm_container.holder.holder_object,
                                 resourcegroup, share)
            dbdisk = VirtualDisk(device_name=disk, controller_type=controller,
                                 bootable=boot, capacity=size, address=address,
                                 snapshotable=snapshot, comments=comments)

            dbshare.disks.append(dbdisk)
        elif filesystem:
            if not dbmachine.vm_container:
                raise ArgumentError("{0} is not a virtual machine, it is not "
                                    "possible to define a virtual disk."
                                    .format(dbmachine))

            dbfs = Filesystem.get_unique(session, name=filesystem,
                                         holder=dbmachine.vm_container.holder,
                                         compel=True)

            dbdisk = VirtualLocalDisk(device_name=disk,
                                      controller_type=controller, bootable=boot,
                                      capacity=size, address=address,
                                      snapshotable=snapshot,
                                      comments=comments)
            dbfs.disks.append(dbdisk)

        else:
            dbdisk = LocalDisk(device_name=disk, controller_type=controller,
                               capacity=size, bootable=boot, comments=comments)

        dbmachine.disks.append(dbdisk)

        plenary_info = Plenary.get_plenary(dbmachine, logger=logger)
        plenary_info.write()

        return
