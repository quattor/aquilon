# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `aq refresh windows hosts`."""

import sqlite3

from aquilon.exceptions_ import (PartialError, InternalError, AquilonError,
                                 ArgumentError)
from aquilon.aqdb.types import MACAddress
from aquilon.aqdb.model import (Host, Interface, Machine, Domain, Archetype,
                                Personality, DnsRecord, OperatingSystem,
                                ReservedName, Fqdn)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.aqdb.model.hostlifecycle import Ready
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.service_instance import check_no_provided_service
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.locks import SyncKey


class CommandRefreshWindowsHosts(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, dryrun, **arguments):
        containers = set()
        partial_error = None
        with SyncKey("windows", logger=logger):
            try:
                self.refresh_windows_hosts(session, logger, containers)
                if dryrun:
                    session.rollback()
                    return
                session.commit()
            except PartialError as e:
                if dryrun:
                    raise
                partial_error = e
                # All errors were caught before hitting the session, so
                # keep going with whatever was successful.
                session.commit()

        if containers:
            plenaries = PlenaryCollection(logger=logger)
            for container in containers:
                plenaries.append(Plenary.get_plenary(container))
            plenaries.write()
        if partial_error:
            raise partial_error
        return

    def refresh_windows_hosts(self, session, logger, containers):
        conn = sqlite3.connect(self.config.get("broker", "windows_host_info"))
        # Enable dictionary-style access to the rows.
        conn.row_factory = sqlite3.Row

        windows_hosts = {}
        interfaces = {}
        cur = conn.cursor()
        # There are more fields in the dataset like machine and
        # aqhostname that might be useful for error messages but these
        # are sufficient.
        cur.execute("select ether, windowshostname from machines")
        for row in cur:
            host = row["windowshostname"]
            if host:
                host = host.strip().lower()
            else:
                continue
            if row["ether"]:
                mac = MACAddress(row["ether"])
            else:
                mac = None
            windows_hosts[host] = mac
            interfaces[mac] = host

        success = []
        failed = []

        q = session.query(Host)
        q = q.filter_by(comments='Created by refresh_windows_host')
        for dbhost in q.all():
            dbmachine = dbhost.hardware_entity
            mac_addresses = [iface.mac for iface in dbmachine.interfaces]
            if dbhost.fqdn in windows_hosts and \
               windows_hosts[dbhost.fqdn] in mac_addresses:
                # All is well
                continue
            try:
                check_no_provided_service(dbhost)
            except ArgumentError as err:
                msg = "Skipping removal of host %s due to: %s" % \
                    (dbhost.fqdn, err)
                failed.append(msg)
                logger.info(msg)
                continue
            success.append("Removed host entry for %s (%s)" %
                           (dbmachine.label, dbmachine.fqdn))
            if dbmachine.vm_container:
                containers.add(dbmachine.vm_container)
            logger.info("Deleting {0:l} (machine {1.label})"
                        .format(dbhost, dbmachine))
            session.delete(dbhost)
            dbdns_rec = dbmachine.primary_name
            dbmachine.primary_name = None
            delete_dns_record(dbdns_rec)
        session.flush()
        # The Host() creations below fail when autoflush is enabled.
        session.autoflush = False

        dbdomain = Domain.get_unique(session,
                                     self.config.get("archetype_windows",
                                                     "host_domain"),
                                     compel=InternalError)
        dbarchetype = Archetype.get_unique(session, "windows",
                                           compel=InternalError)
        dbpersonality = Personality.get_unique(session, archetype=dbarchetype,
                                               name="generic",
                                               compel=InternalError)
        dbstatus = Ready.get_instance(session)
        dbos = OperatingSystem.get_unique(session, name="windows",
                                          version="generic",
                                          archetype=dbarchetype,
                                          compel=InternalError)
        for (host, mac) in windows_hosts.items():
            try:
                (short, dbdns_domain) = parse_fqdn(session, host)
            except AquilonError as err:
                msg = "Skipping host %s: %s" % (host, err)
                failed.append(msg)
                logger.info(msg)
                continue
            existing = DnsRecord.get_unique(session, name=short,
                                            dns_domain=dbdns_domain)
            if existing:
                if not existing.hardware_entity:
                    msg = "Skipping host %s: It is not a primary name." % host
                    failed.append(msg)
                    logger.info(msg)
                    continue
                # If these are invalid there should have been a deletion
                # attempt above.
                if not existing.hardware_entity.interfaces:
                    msg = "Skipping host %s: Host already exists but has " \
                        "no interface attached." % host
                    failed.append(msg)
                    logger.info(msg)
                elif existing.hardware_entity.interfaces[0].mac != mac:
                    msg = "Skipping host %s: Host already exists but with " \
                        "MAC address %s and not %s." % \
                        (host, existing.hardware_entity.interfaces[0].mac, mac)
                    failed.append(msg)
                    logger.info(msg)
                continue
            dbinterface = session.query(Interface).filter_by(mac=mac).first()
            if not dbinterface:
                msg = "Skipping host %s: MAC address %s is not present in " \
                    "AQDB." % (host, mac)
                failed.append(msg)
                logger.info(msg)
                continue
            q = session.query(Machine)
            q = q.filter_by(id=dbinterface.hardware_entity.id)
            dbmachine = q.first()
            if not dbmachine:
                msg = "Skipping host %s: The AQDB interface with MAC address " \
                    "%s is tied to hardware %s instead of a virtual " \
                    "machine." % (host, mac, dbinterface.hardware_entity.label)
                failed.append(msg)
                logger.info(msg)
                continue
            if dbinterface.assignments:
                msg = "Skipping host %s: The AQDB interface with MAC address " \
                    "%s is already tied to %s." % \
                    (host, mac, dbinterface.assignments[0].fqdns[0])
                failed.append(msg)
                logger.info(msg)
                continue
            if dbmachine.host:
                msg = "Skipping host %s: The AQDB interface with MAC address " \
                    "%s is already tied to %s." % (host, mac, dbmachine.fqdn)
                failed.append(msg)
                logger.info(msg)
                continue
            dbhost = Host(hardware_entity=dbmachine, branch=dbdomain,
                          status=dbstatus,
                          personality=dbpersonality, operating_system=dbos,
                          comments="Created by refresh_windows_host")
            session.add(dbhost)

            dbfqdn = Fqdn.get_or_create(session, name=short,
                                        dns_domain=dbdns_domain, preclude=True)
            dbdns_rec = ReservedName(fqdn=dbfqdn)
            session.add(dbdns_rec)
            dbmachine.primary_name = dbdns_rec
            success.append("Added host entry for %s (%s)." %
                           (dbmachine.label, dbdns_rec.fqdn))
            logger.info("Added {0:l} to machine {1.label}".format(dbhost,
                                                                  dbmachine))
            if dbmachine.vm_container:
                containers.add(dbmachine.vm_container)
            session.flush()

        session.flush()
        if failed:
            raise PartialError(success, failed)

        return
