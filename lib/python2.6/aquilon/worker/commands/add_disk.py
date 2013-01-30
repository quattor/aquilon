# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Contains the logic for `aq add disk`."""

import re

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.service_instance import get_service_instance
from aquilon.aqdb.model import (LocalDisk, NasDisk, Service, Machine, Share,
                                VirtualDisk, ResourceGroup)
from aquilon.aqdb.model.disk import controller_types
from aquilon.worker.templates.machine import PlenaryMachineInfo


class CommandAddDisk(BrokerCommand):
    """Add a disk object (local or share) to a machine"""
    # FIXME: add "controller" and "size" once the deprecated alternatives are
    # removed
    required_parameters = ["machine", "disk"]

    REGEX_ADDRESS = re.compile("\d+:\d+$")

    def _check_disk_address(self, address):
        if not CommandAddDisk.REGEX_ADDRESS.match(address):
            raise ArgumentError("Disk address '%s' is not valid, it must "
                                "match \d+:\d+ (e.g. 0:0)." % address)

    def _write_plenary_info(self, dbmachine, logger):
        """write template files"""
        plenary_info = PlenaryMachineInfo(dbmachine, logger=logger)
        plenary_info.write()

    def render(self, session, logger, machine, disk, controller,
               share, resourcegroup,
               address, comments, dbuser, size, boot, **kw):

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

        if dbmachine.vm_container and \
           hasattr(dbmachine.vm_container.holder.holder_object, 'metacluster'):
            dbmetacluster = dbmachine.vm_container.holder.holder_object.metacluster
        else:
            dbmetacluster = None

        if resourcegroup:

            if not dbmachine.cluster or not dbmetacluster:
                raise ArgumentError("Machine %s should be contained by a "
                                    "cluster")

            dbrg = ResourceGroup.get_unique(session, name=resourcegroup,
                                    holder=dbmachine.cluster.resholder,
                                    compel=False)

            if not dbrg:
                if dbmetacluster:
                    dbrg = ResourceGroup.get_unique(session,
                                    name=resourcegroup,
                                    holder=dbmetacluster.resholder,
                                    compel=True)
                else:
                    raise NotFoundException("resourcegroup %s in %s "
                                "not found." %
                                (resourcegroup, dbmachine.cluster.name))

            dbshare = Share.get_unique(session,
                                       name=share,
                                       holder=dbrg.resholder,
                                       compel=True)

            dbdisk = VirtualDisk(device_name=disk,
                                 controller_type=controller,
                                 bootable=boot,
                                 capacity=size, address=address,
                                 comments=comments)

            dbmachine.disks.append(dbdisk)
            dbshare.disks.append(dbdisk)

        else:
            if share:
                dbservice = Service.get_unique(session, "nas_disk_share",
                                               compel=True)
                dbshare = get_service_instance(session, dbservice, share)

                self._check_disk_address(address)

                dbdisk = NasDisk(device_name=disk,
                                 controller_type=controller,
                                 bootable=boot, service_instance=dbshare,
                                 capacity=size, address=address,
                                 comments=comments)
            else:
                dbdisk = LocalDisk(device_name=disk,
                                   controller_type=controller,
                                   capacity=size, bootable=boot,
                                   comments=comments)
            dbmachine.disks.append(dbdisk)

        if dbmetacluster:
            dbmetacluster.validate()

        self._write_plenary_info(dbmachine, logger)
        return
