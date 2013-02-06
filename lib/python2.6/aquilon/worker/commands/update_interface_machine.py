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
"""Contains the logic for `aq update interface --machine`."""


from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.interface import (verify_port_group,
                                                 choose_port_group,
                                                 assign_address,
                                                 rename_interface)
from aquilon.worker.locks import lock_queue
from aquilon.worker.templates.machine import PlenaryMachineInfo
from aquilon.worker.processes import DSDBRunner
from aquilon.aqdb.model import Machine, Interface, Model
from aquilon.utils import first_of


class CommandUpdateInterfaceMachine(BrokerCommand):

    required_parameters = ["interface", "machine"]

    def render(self, session, logger, interface, machine, mac, model, vendor,
               boot, pg, autopg, comments, master, clear_master, default_route,
               rename_to, **arguments):
        """This command expects to locate an interface based only on name
        and machine - all other fields, if specified, are meant as updates.

        If the machine has a host, dsdb may need to be updated.

        The boot flag can *only* be set to true.  This is mostly technical,
        as at this point in the interface it is difficult to tell if the
        flag was unset or set to false.  However, it also vastly simplifies
        the dsdb logic - we never have to worry about a user trying to
        remove the boot flag from a host in dsdb.

        """

        audit_results = []

        dbhw_ent = Machine.get_unique(session, machine, compel=True)
        dbinterface = Interface.get_unique(session, hardware_entity=dbhw_ent,
                                           name=interface, compel=True)

        oldinfo = DSDBRunner.snapshot_hw(dbhw_ent)

        if arguments.get('hostname', None):
            # Hack to set an intial interface for an aurora host...
            dbhost = dbhw_ent.host
            if dbhost.archetype.name == 'aurora' and \
               dbhw_ent.primary_ip and not dbinterface.addresses:
                assign_address(dbinterface, dbhw_ent.primary_ip,
                               dbhw_ent.primary_name.network)

        # We may need extra IP verification (or an autoip option)...
        # This may also throw spurious errors if attempting to set the
        # port_group to a value it already has.
        if pg is not None and dbinterface.port_group != pg.lower().strip():
            dbinterface.port_group = verify_port_group(
                dbinterface.hardware_entity, pg)
        elif autopg:
            dbinterface.port_group = choose_port_group(
                session, dbinterface.hardware_entity)
            audit_results.append(('pg', dbinterface.port_group))

        if master:
            if dbinterface.addresses:
                # FIXME: as a special case, if the only address is the
                # primary IP, then we could just move it to the master
                # interface. However this can be worked around by bonding
                # the interface before calling "add host", so don't bother
                # for now.
                raise ArgumentError("Can not enslave {0:l} because it has "
                                    "addresses.".format(dbinterface))
            dbmaster = Interface.get_unique(session, hardware_entity=dbhw_ent,
                                            name=master, compel=True)
            if dbmaster in dbinterface.all_slaves():
                raise ArgumentError("Enslaving {0:l} would create a circle, "
                                    "which is not allowed.".format(dbinterface))
            dbinterface.master = dbmaster

        if clear_master:
            if not dbinterface.master:
                raise ArgumentError("{0} is not a slave.".format(dbinterface))
            dbinterface.master = None

        if comments:
            dbinterface.comments = comments
        if boot:
            # Should we also transfer the primary IP to the new boot interface?
            # That could get tricky if the new interface already has an IP
            # address...
            for i in dbhw_ent.interfaces:
                if i == dbinterface:
                    i.bootable = True
                    i.default_route = True
                else:
                    i.bootable = False
                    i.default_route = False
        if default_route is not None:
            dbinterface.default_route = default_route
            if not first_of(dbhw_ent.interfaces, lambda x: x.default_route):
                logger.client_info("Warning: {0:l} has no default route, hope "
                                   "that's ok.".format(dbhw_ent))

        #Set this mac address last so that you can update to a bootable
        #interface *before* adding a mac address. This is so the validation
        #that takes place in the interface class doesn't have to be worried
        #about the order of update to bootable=True and mac address
        if mac:
            q = session.query(Interface).filter_by(mac=mac)
            other = q.first()
            if other and other != dbinterface:
                raise ArgumentError("MAC address {0} is already in use by "
                                    "{1:l}.".format(mac, other))
            dbinterface.mac = mac

        if model or vendor:
            if not dbinterface.model_allowed:
                raise ArgumentError("Model/vendor can not be set for a {0:lc}."
                                    .format(dbinterface))

            dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                       machine_type='nic', compel=True)
            dbinterface.model = dbmodel
        if rename_to:
            rename_interface(session, dbinterface, rename_to)

        session.flush()
        session.refresh(dbhw_ent)

        plenary_info = PlenaryMachineInfo(dbhw_ent, logger=logger)
        key = plenary_info.get_write_key()
        try:
            lock_queue.acquire(key)
            plenary_info.write(locked=True)

            if dbhw_ent.host and dbhw_ent.host.archetype.name != "aurora":
                dsdb_runner = DSDBRunner(logger=logger)
                dsdb_runner.update_host(dbhw_ent, oldinfo)
                dsdb_runner.commit_or_rollback()
        except AquilonError, err:
            plenary_info.restore_stash()
            raise ArgumentError(err)
        except:
            plenary_info.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        for name, value in audit_results:
            self.audit_result(session, name, value, **arguments)
        return
