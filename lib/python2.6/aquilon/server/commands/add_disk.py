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
from aquilon.server.broker import BrokerCommand, force_int
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.dbwrappers.service_instance import get_service_instance
from aquilon.aqdb.model import Disk, LocalDisk, NasDisk, Service
from aquilon.aqdb.model.disk import controller_types
from aquilon.server.templates.machine import PlenaryMachineInfo

class CommandAddDisk(BrokerCommand):

    required_parameters = ["machine", "disk", "type", "capacity"]

    def render(self, session, logger, machine, disk, type, capacity, share,
               address, comments, user, **arguments):

        dbmachine = get_machine(session, machine)
        d = session.query(Disk).filter_by(machine=dbmachine, device_name=disk).all()
        if (len(d) != 0):
            raise ArgumentError("machine %s already has a disk named %s"%(machine,disk))

        if type not in controller_types:
            raise ArgumentError("%s is not a valid controller type %s" %
                                (type, controller_types))

        capacity = force_int("capacity", capacity)
        if share:
            dbservice = Service.get_unique(session, "nas_disk_share",
                                           compel=True)
            dbshare = get_service_instance(session, dbservice, share)
            if not re.compile("\d+:\d+$").match(address):
                raise ArgumentError("disk address '%s' is illegal: must be " \
                                    "\d+:\d+ (e.g. 0:0)" % address)
            if dbmachine.cluster and dbmachine.cluster.metacluster:
                dbmetacluster = dbmachine.cluster.metacluster
                shares = dbmetacluster.shares
                if dbshare not in shares and \
                   len(shares) >= dbmetacluster.max_shares:
                    raise ArgumentError("Adding a disk on a new share for %s "
                                        "would exceed the metacluster's "
                                        "max_shares (%s)" %
                                        (dbmetacluster.name,
                                         dbmetacluster.max_shares))
            dbdisk = NasDisk(machine=dbmachine,
                             device_name=disk,
                             controller_type=type,
                             service_instance=dbshare,
                             capacity=capacity,
                             address=address,
                             comments=comments)
        else:
            dbdisk = LocalDisk(machine=dbmachine, device_name=disk,
                controller_type=type, capacity=capacity, comments=comments)
        try:
            session.add(dbdisk)
        except InvalidRequestError, e:
            raise ArgumentError("Could not add disk: %s" % e)

        plenary_info = PlenaryMachineInfo(dbmachine, logger=logger)
        plenary_info.write()
        return
