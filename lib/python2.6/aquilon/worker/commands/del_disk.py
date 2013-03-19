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
"""Contains the logic for `aq del disk`."""

from aquilon.exceptions_ import ArgumentError, NotFoundException, AquilonError
from aquilon.aqdb.model import Disk, Machine
from aquilon.aqdb.model.disk import controller_types
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.templates.base import Plenary
from aquilon.worker.locks import lock_queue, CompileKey


class CommandDelDisk(BrokerCommand):

    required_parameters = ["machine"]

    def render(self, session, logger, machine, disk, controller, size, all,
               dbuser, **arguments):

        # Handle deprecated arguments
        if arguments.get("type", None):
            self.deprecated_option("type", "Please use --controller instead.",
                                   logger=logger, **arguments)
            controller = arguments["type"]
        if arguments.get("capacity", None):
            self.deprecated_option("capacity", "Please use --size instead.",
                                   logger=logger, **arguments)
            size = arguments["capacity"]

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

        plenary_machine = Plenary.get_plenary(dbmachine, logger=logger)
        key = plenary_machine.get_write_key()
        dbcontainer = dbmachine.vm_container
        if dbcontainer:
            plenary_container = Plenary.get_plenary(dbcontainer, logger=logger)
            key = CompileKey.merge([key, plenary_container.get_write_key()])
        try:
            lock_queue.acquire(key)
            if dbcontainer:
                plenary_container.write(locked=True)
            plenary_machine.write(locked=True)
        except:
            plenary_machine.restore_stash()
            if dbcontainer:
                plenary_container.restore_stash()
            raise
        finally:
            lock_queue.release(key)
