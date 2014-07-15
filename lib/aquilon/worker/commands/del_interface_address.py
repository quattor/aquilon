# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `aq del interface address`."""

from functools import partial

from aquilon.worker.broker import BrokerCommand
from aquilon.exceptions_ import ArgumentError, IncompleteError
from aquilon.aqdb.model import (HardwareEntity, Interface, AddressAssignment,
                                DnsDomain, Fqdn, ARecord, NetworkEnvironment)
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.service_instance import check_no_provided_service
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.templates import Plenary
from aquilon.utils import first_of


class CommandDelInterfaceAddress(BrokerCommand):

    required_parameters = ['interface']

    def render(self, session, logger, machine, chassis, network_device, interface,
               fqdn, ip, label, keep_dns, network_environment,
               **kwargs):

        if machine:
            hwtype = 'machine'
            hwname = machine
        elif chassis:
            hwtype = 'chassis'
            hwname = chassis
        elif network_device:
            hwtype = 'network_device'
            hwname = network_device

        dbhw_ent = HardwareEntity.get_unique(session, hwname,
                                             hardware_type=hwtype, compel=True)
        dbinterface = Interface.get_unique(session, hardware_entity=dbhw_ent,
                                           name=interface, compel=True)
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)

        oldinfo = DSDBRunner.snapshot_hw(dbhw_ent)

        if fqdn:
            dbdns_rec = ARecord.get_unique(session, fqdn=fqdn,
                                           dns_environment=dbnet_env.dns_environment,
                                           compel=True)
            ip = dbdns_rec.ip

        addr = None
        if ip:
            addr = first_of(dbinterface.assignments, lambda x: x.ip == ip)
            if not addr:
                raise ArgumentError("{0} does not have IP address {1} assigned to "
                                    "it.".format(dbinterface, ip))
        elif label is not None:
            addr = first_of(dbinterface.assignments, lambda x: x.label == label)
            if not addr:
                raise ArgumentError("{0} does not have an address with label "
                                    "{1}.".format(dbinterface, label))

        if not addr:
            raise ArgumentError("Please specify the address to be removed "
                                "using either --ip, --label, or --fqdn.")

        dbnetwork = addr.network
        ip = addr.ip

        # Lock order: DNS domain(s), network
        q = session.query(DnsDomain.id)
        q = q.join(Fqdn, (ARecord, ARecord.fqdn_id == Fqdn.id))
        q = q.filter_by(network=dbnetwork, ip=ip)
        q = q.order_by(DnsDomain.id)
        q = q.with_lockmode("update")
        session.execute(q)
        dbnetwork.lock_row()

        if dbnetwork.network_environment != dbnet_env:
            raise ArgumentError("The specified address lives in {0:l}, not in "
                                "{1:l}.  Use the --network_environment option "
                                "to select the correct environment."
                                .format(dbnetwork.network_environment, dbnet_env))

        # Forbid removing the primary name
        if ip == dbhw_ent.primary_ip:
            raise ArgumentError("The primary IP address of a hardware entity "
                                "cannot be removed.")

        check_no_provided_service(addr)

        dbinterface.assignments.remove(addr)

        # Check if the address was assigned to multiple interfaces, and remove
        # the DNS entries if this was the last use
        q = session.query(AddressAssignment)
        q = q.filter_by(network=dbnetwork, ip=ip)
        other_uses = q.all()
        if not other_uses and not keep_dns:
            q = session.query(ARecord)
            q = q.filter_by(network=dbnetwork, ip=ip)
            q = q.join(ARecord.fqdn)
            q = q.filter_by(dns_environment=dbnet_env.dns_environment)
            map(partial(delete_dns_record, locked=True), q.all())

        session.flush()

        dbhost = getattr(dbhw_ent, "host", None)
        if dbhost:
            plenary_info = Plenary.get_plenary(dbhost, logger=logger)
            with plenary_info.get_key():
                try:
                    try:
                        plenary_info.write(locked=True)
                    except IncompleteError:
                        # FIXME: if this command is used after "add host" but
                        # before "make", then writing out the template will fail
                        # due to required services not being assigned. Ignore
                        # this error for now.
                        plenary_info.restore_stash()

                    dsdb_runner = DSDBRunner(logger=logger)
                    if dbhost.archetype.name == 'aurora':
                        logger.client_info("WARNING: removing IP %s from AQDB and "
                                           "*not* changing DSDB." % ip)
                    else:
                        dsdb_runner.update_host(dbhw_ent, oldinfo)

                        if not other_uses and keep_dns:
                            q = session.query(ARecord)
                            q = q.filter_by(network=dbnetwork)
                            q = q.filter_by(ip=ip)
                            dbdns_rec = q.first()
                            dsdb_runner.add_host_details(dbdns_rec.fqdn, ip)

                        dsdb_runner.commit_or_rollback("Could not add host to DSDB")
                except:
                    plenary_info.restore_stash()
                    raise
        else:
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.update_host(dbhw_ent, oldinfo)
            dsdb_runner.commit_or_rollback("Could not add host to DSDB")

        return
