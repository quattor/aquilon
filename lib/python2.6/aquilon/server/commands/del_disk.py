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
"""Contains the logic for `aq del disk`."""


from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import Disk
from aquilon.aqdb.model.disk import controller_types
from aquilon.server.broker import BrokerCommand, force_int
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.templates.machine import PlenaryMachineInfo


class CommandDelDisk(BrokerCommand):

    required_parameters = ["machine"]

    def render(self, session, logger, machine, disk, type, capacity, all, user,
               **arguments):
        dbmachine = get_machine(session, machine)
        q = session.query(Disk).filter_by(machine=dbmachine)
        if disk:
            q = q.filter_by(device_name=disk)
        if type:
            if type not in controller_types:
                raise ArgumentError("%s is not a valid controller type %s" %
                                    (type, controller_types))
            q = q.filter_by(controller_type=type)
        if capacity:
            capacity = force_int("capacity", capacity)
            q = q.filter_by(capacity=capacity)
        results = q.all()
        if len(results) == 1:
            session.delete(results[0])
        elif len(results) == 0:
            raise NotFoundException("No disks found.")
        elif all:
            for result in results:
                session.delete(result)
        else:
            raise ArgumentError("More than one matching disk found.  Use --all to delete them all.")
        session.flush()
        session.refresh(dbmachine)

        plenary_info = PlenaryMachineInfo(dbmachine, logger=logger)
        plenary_info.write()
        return
