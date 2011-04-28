# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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

from aquilon.exceptions_ import (ArgumentError, NotFoundException,
                                 ProcessException, AquilonError)
from aquilon.aqdb.model import Disk, Machine
from aquilon.aqdb.model.disk import controller_types
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates.machine import PlenaryMachineInfo
from aquilon.worker.templates.cluster import PlenaryCluster
from aquilon.worker.processes import NASAssign
from aquilon.worker.locks import lock_queue, CompileKey


class CommandDelDisk(BrokerCommand):

    required_parameters = ["machine"]

    def render(self, session, logger, machine, disk, controller, size, all,
               dbuser,  **arguments):

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
        to_remove_from_rp = None
        uname = str(dbuser.name)
        for dbdisk in results:
            if hasattr(dbdisk, 'service_instance') and (
                dbdisk.service_instance.manager == 'resourcepool'):
                na_obj = NASAssign(machine=machine, disk=dbdisk.device_name,
                                   owner=uname)
                if to_remove_from_rp:
                    raise ArgumentError('Multiple managed shares must be '
                                        'removed as seperate operations. '
                                        'Please run "del_disk" individually for '
                                        'the following shares: %s '
                                        % " ,".join(to_remove_from_rp))
                else:
                    to_remove_from_rp = na_obj
        if len(results) == 1:
            session.delete(results[0])
        elif len(results) == 0:
            raise NotFoundException("No disks found.")
        elif all:
            for result in results:
                session.delete(result)
        else:
            raise ArgumentError("More than one matching disks found.  "
                                "Use --all to delete them all.")
        session.flush()
        session.expire(dbmachine, ['disks'])

        plenary_machine = PlenaryMachineInfo(dbmachine, logger=logger)
        key = plenary_machine.get_write_key()
        dbcluster = dbmachine.cluster
        if dbcluster:
            plenary_cluster = PlenaryCluster(dbcluster, logger=logger)
            key = CompileKey.merge([key, plenary_cluster.get_write_key()])
        try:
            lock_queue.acquire(key)
            if dbcluster:
                plenary_cluster.write(locked=True)
            plenary_machine.write(locked=True)
            if to_remove_from_rp:
                self._remove_from_rp(to_remove_from_rp)
        except:
            plenary_machine.restore_stash()
            if dbcluster:
                plenary_cluster.restore_stash()
            raise
        finally:
            lock_queue.release(key)

    def _remove_from_rp(self, na_obj):
        try:
            na_obj.delete()
        except Exception, e:
            raise AquilonError('Failed while removing nas assignment in '
                               'resource pool: %s' % e)
        return
