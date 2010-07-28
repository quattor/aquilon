# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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

from sqlalchemy.exceptions import InvalidRequestError
from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.service_instance import get_service_instance
from aquilon.aqdb.model import Disk, LocalDisk, NasDisk, Service, Machine
from aquilon.aqdb.model.disk import controller_types
from aquilon.server.templates.machine import PlenaryMachineInfo

class CommandAddDisk(BrokerCommand):

    # FIXME: add "controller" and "size" once the deprecated alternatives are
    # removed
    required_parameters = ["machine", "disk"]

    def render(self, session, logger, machine, disk, controller, size, share,
               address, comments, user, **arguments):

        # Handle deprecated arguments
        if arguments.get("type", None):
            controller = arguments["type"]
        if arguments.get("capacity", None):
            size = arguments["capacity"]
        if not size or not controller:
            raise ArgumentError("Please specify both --size and --controller.")

        dbmachine = Machine.get_unique(session, machine, compel=True)
        d = session.query(Disk).filter_by(machine=dbmachine, device_name=disk).all()
        if (len(d) != 0):
            raise ArgumentError("Machine %s already has a disk named %s." %
                                (machine,disk))

        if controller not in controller_types:
            raise ArgumentError("%s is not a valid controller type, use one "
                                "of: %s." % (controller,
                                             ", ".join(controller_types)))

        dbmetacluster = None
        if share:
            dbservice = Service.get_unique(session, "nas_disk_share",
                                           compel=True)
            dbshare = get_service_instance(session, dbservice, share)
            if not re.compile("\d+:\d+$").match(address):
                raise ArgumentError("Disk address '%s' is not valid, it must "
                                    "match \d+:\d+ (e.g. 0:0)." % address)
            if dbmachine.cluster:
                dbmetacluster = dbmachine.cluster.metacluster
            max_clients = dbshare.enforced_max_clients
            current_clients = len(dbshare.nas_disks)
            if max_clients is not None and current_clients >= max_clients:
                raise ArgumentError("NAS share %s is full (%s/%s)" %
                                    (dbshare.name, current_clients,
                                     max_clients))
            dbdisk = NasDisk(machine=dbmachine,
                             device_name=disk,
                             controller_type=controller,
                             service_instance=dbshare,
                             capacity=size,
                             address=address,
                             comments=comments)
        else:
            dbdisk = LocalDisk(machine=dbmachine, device_name=disk,
                               controller_type=controller, capacity=size,
                               comments=comments)
        try:
            session.add(dbdisk)
            session.flush()
            if dbmetacluster:
                dbmetacluster.validate()
        except InvalidRequestError, e:
            raise ArgumentError("Could not add disk: %s" % e)

        plenary_info = PlenaryMachineInfo(dbmachine, logger=logger)
        plenary_info.write()
        return
