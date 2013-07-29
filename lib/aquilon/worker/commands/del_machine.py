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
"""Contains the logic for `aq del machine`."""

from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.locks import lock_queue, CompileKey
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.aqdb.model import Machine


class CommandDelMachine(BrokerCommand):

    required_parameters = ["machine"]

    def render(self, session, logger, machine, dbuser, **arguments):
        dbmachine = Machine.get_unique(session, machine, compel=True)

        remove_plenaries = PlenaryCollection(logger=logger)
        remove_plenaries.append(Plenary.get_plenary(dbmachine))
        if dbmachine.vm_container:
            remove_plenaries.append(Plenary.get_plenary(dbmachine.vm_container))
            dbcontainer = dbmachine.vm_container.holder.holder_object
        else:
            dbcontainer = None

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

        session.delete(dbmachine)
        session.flush()

        key = remove_plenaries.get_remove_key()
        if dbcontainer:
            plenary_container = Plenary.get_plenary(dbcontainer, logger=logger)
            key = CompileKey.merge([key, plenary_container.get_write_key()])
        try:
            lock_queue.acquire(key)
            remove_plenaries.stash()
            if dbcontainer:
                plenary_container.write(locked=True)
            remove_plenaries.remove(locked=True)
        except:
            remove_plenaries.restore_stash()
            if dbcontainer:
                plenary_container.restore_stash()
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
