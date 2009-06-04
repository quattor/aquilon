# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.broker import BrokerCommand, force_int
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.dbwrappers.disk_type import get_disk_type
from aquilon.aqdb.model import Disk
from aquilon.server.templates.machine import PlenaryMachineInfo


class CommandAddDisk(BrokerCommand):

    required_parameters = ["machine", "disk", "type", "capacity"]

    def render(self, session, machine, disk, type, capacity, comments,
            user, **arguments):

        dbmachine = get_machine(session, machine)
        d = session.query(Disk).filter_by(machine=dbmachine, device_name=disk).all()
        if (len(d) != 0):
            raise ArgumentError("machine %s already has a disk named %s"%(machine,disk))

        capacity = force_int("capacity", capacity)
        dbdisk_type = get_disk_type(session, type)
        dbdisk = Disk(machine=dbmachine, device_name=disk,
                disk_type=dbdisk_type, capacity=capacity, comments=comments)
        try:
            session.add(dbdisk)
        except InvalidRequestError, e:
            raise ArgumentError("Could not add disk: %s" % e)

        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write()
        return


