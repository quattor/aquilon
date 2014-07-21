# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `aq update interface --machine`."""

from aquilon.aqdb.types import NicType
from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.aqdb.model import Machine, Interface, Model
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.interface import (verify_port_group,
                                                 choose_port_group,
                                                 assign_address,
                                                 rename_interface)
from aquilon.worker.templates import Plenary, PlenaryCollection
from aquilon.worker.processes import DSDBRunner
from aquilon.utils import first_of


class CommandUpdateInterfaceMachine(BrokerCommand):

    required_parameters = ["interface", "machine"]

    def render(self, session, logger, interface, machine, mac, model, vendor,
               boot, pg, autopg, comments, master, clear_master, default_route,
               rename_to, bus_address, **arguments):
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
                               dbhw_ent.primary_name.network, logger=logger)

        # We may need extra IP verification (or an autoip option)...
        # This may also throw spurious errors if attempting to set the
        # port_group to a value it already has.
        if pg is not None and dbinterface.port_group_name != pg.lower().strip():
            dbinterface.port_group_name = verify_port_group(
                dbinterface.hardware_entity, pg)
        elif autopg:
            dbinterface.port_group_name = choose_port_group(
                logger, dbinterface.hardware_entity)
            audit_results.append(('pg', dbinterface.port_group_name))

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

        if comments is not None:
            dbinterface.comments = comments

        if bus_address is not None:
            dbinterface.bus_address = bus_address

        if boot:
            # Figure out if the current bootble interface also has the
            # default route set; the new bootable interface probably
            # wants to have the same settings.  Note that if
            # old_default_route is None there was no bootable interface.
            old_default_route = None
            for i in dbhw_ent.interfaces:
                if i.bootable:
                    old_default_route = i.default_route
                    break

            # Apply the bootable flag to the supplied interface, clearing
            # it on all other interfaces.
            for i in dbhw_ent.interfaces:
                if i == dbinterface:
                    i.bootable = True
                else:
                    i.bootable = False

            # If the user was not explicit about the default route flag
            # (default_route is None); there was an existing bootable
            # interface (old_default_route is not None); the new default
            # route setting differs from the old - then produce a warning.
            if (default_route is None and
                old_default_route is not None and
                dbinterface.default_route != old_default_route):
                if old_default_route:
                    logger.client_info("Warning: New boot interface {0} is no "
                                       "longer provides the default route; it "
                                       "did before!".format(dbinterface))
                else:
                    logger.client_info("Warning: New boot interface {0} now "
                                       "provides the default route; it didn't "
                                       "before!".format(dbinterface))

            # Should we also transfer the primary IP to the new boot interface?
            # That could get tricky if the new interface already has an IP
            # address...

        if default_route is not None:
            dbinterface.default_route = default_route
            if not first_of(dbhw_ent.interfaces, lambda x: x.default_route):
                logger.client_info("Warning: {0:l} has no default route, hope "
                                   "that's ok.".format(dbhw_ent))

        # Set this mac address last so that you can update to a bootable
        # interface *before* adding a mac address. This is so the validation
        # that takes place in the interface class doesn't have to be worried
        # about the order of update to bootable=True and mac address
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
                                       model_type=NicType.Nic, compel=True)
            dbinterface.model = dbmodel
        if rename_to:
            rename_interface(session, dbinterface, rename_to)

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbhw_ent))
        # Interface renaming affects the host and service addresses
        if dbhw_ent.host:
            plenaries.append(Plenary.get_plenary(dbhw_ent.host))
        for addr in dbinterface.assignments:
            if addr.service_address:
                plenaries.append(Plenary.get_plenary(addr.service_address))

        with plenaries.get_key():
            try:
                plenaries.write(locked=True)

                if dbhw_ent.host and dbhw_ent.host.archetype.name != "aurora":
                    dsdb_runner = DSDBRunner(logger=logger)
                    dsdb_runner.update_host(dbhw_ent, oldinfo)
                    dsdb_runner.commit_or_rollback()
            except AquilonError as err:
                plenaries.restore_stash()
                raise ArgumentError(err)
            except:
                plenaries.restore_stash()
                raise

        for name, value in audit_results:
            self.audit_result(session, name, value, **arguments)
        return
