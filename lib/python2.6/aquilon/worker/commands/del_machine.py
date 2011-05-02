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
"""Contains the logic for `aq del machine`."""

from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.locks import lock_queue, CompileKey
from aquilon.worker.templates.machine import PlenaryMachineInfo
from aquilon.worker.templates.cluster import PlenaryCluster
from aquilon.aqdb.model import Machine
from aquilon.worker.processes import NASAssign

class CommandDelMachine(BrokerCommand):

    required_parameters = ["machine"]

    def render(self, session, logger, machine, user, dbuser, **arguments):
        dbmachine = Machine.get_unique(session, machine, compel=True)
        plenary_machine = PlenaryMachineInfo(dbmachine, logger=logger)
        dbcluster = dbmachine.cluster

        if dbmachine.host:
            raise ArgumentError("{0} is still in use by {1:l} and cannot be "
                                "deleted.".format(dbmachine, dbmachine.host))
        addrs = []
        for addr in dbmachine.all_addresses():
            addrs.append("%s: %s" % (addr.logical_name, addr.ip))
        if addrs:
            addrmsg = ", ".join(addrs)
            raise ArgumentError("{0} still provides the following addresses, "
                                "delete them first: {1}.".format(dbmachine,
                                                                 addrmsg))
        uname = str(dbuser.name)
        to_remove_from_rp = None
        for dbdisk in dbmachine.disks:
            if (hasattr(dbdisk, 'service_instance') and
                dbdisk.service_instance.manager == 'resourcepool'):
                if to_remove_from_rp:
                    raise ArgumentError('Multiple managed shares must be '
                                        'removed as seperate operations. '
                                        'Please run "del_disk" individually for '
                                        'the following shares: %s '
                                        % (" ,".join(to_remove_from_rp)))
                else:
                    na_obj = NASAssign(machine=machine, disk=dbdisk.device_name,
                                       owner=uname)
                    to_remove_from_rp = na_obj
            # Rely on cascade delete to remove the disks.  The Oracle driver
            # can handle the additional/explicit delete request but the
            # sqlite driver can't.
            logger.info("While deleting machine '%s' will remove disk '%s'" %
                        (dbmachine.label, dbdisk.device_name))
            #session.delete(dbdisk)
        session.delete(dbmachine)
        session.flush()

        key = plenary_machine.get_remove_key()
        if dbcluster:
            plenary_cluster = PlenaryCluster(dbcluster, logger=logger)
            key = CompileKey.merge([key, plenary_cluster.get_write_key()])
        try:
            lock_queue.acquire(key)
            plenary_machine.stash()
            if dbcluster:
                plenary_cluster.write(locked=True)
            plenary_machine.remove(locked=True)
            if to_remove_from_rp:
                self._remove_from_rp(to_remove_from_rp)
        except:
            plenary_machine.restore_stash()
            if dbcluster:
                plenary_cluster.restore_stash()
            raise
        finally:
            lock_queue.release(key)
        return

    def _remove_from_rp(self, na_obj):
        try:
            na_obj.delete()
        except Exception, e:
            raise AquilonError('Failed while removing nas assignment in '
                               'resource pool: %s' % e)
        return
