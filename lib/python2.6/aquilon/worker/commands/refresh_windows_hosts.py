# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq refresh windows hosts`."""


import sqlite3

from aquilon.exceptions_ import PartialError, InternalError, AquilonError
from aquilon.aqdb.model import (Host, Interface, Machine, Domain, Archetype,
                                Personality, HostLifecycle, DnsRecord,
                                OperatingSystem, ReservedName, Fqdn)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.host import get_host_dependencies
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.locks import SyncKey


class CommandRefreshWindowsHosts(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, dryrun, **arguments):
        containers = set()
        partial_error = None
        with SyncKey(data="windows", logger=logger):
            try:
                self.refresh_windows_hosts(session, logger, containers)
                if dryrun:
                    session.rollback()
                    return
                session.commit()
            except PartialError, e:
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
            mac = row["ether"]
            if mac:
                mac = mac.strip().lower()
            windows_hosts[host] = mac
            interfaces[mac] = host

        success = []
        failed = []

        q = session.query(Host)
        q = q.filter_by(comments='Created by refresh_windows_host')
        for dbhost in q.all():
            mac_addresses = [iface.mac for iface in dbhost.machine.interfaces]
            if dbhost.fqdn in windows_hosts and \
               windows_hosts[dbhost.fqdn] in mac_addresses:
                # All is well
                continue
            deps = get_host_dependencies(session, dbhost)
            if deps:
                msg = "Skipping removal of host %s with dependencies: %s" % \
                        (dbhost.fqdn, ", ".join(deps))
                failed.append(msg)
                logger.info(msg)
                continue
            dbmachine = dbhost.machine
            success.append("Removed host entry for %s (%s)" %
                           (dbmachine.label, dbmachine.fqdn))
            if dbmachine.vm_container:
                containers.add(dbmachine.vm_container)
            session.delete(dbhost)
            delete_dns_record(dbmachine.primary_name)
            session.expire(dbmachine, ['primary_name'])
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
        dbstatus = HostLifecycle.get_unique(session, "ready",
                                            compel=InternalError)
        dbos = OperatingSystem.get_unique(session, name="windows",
                                          version="generic",
                                          archetype=dbarchetype,
                                          compel=InternalError)
        for (host, mac) in windows_hosts.items():
            try:
                (short, dbdns_domain) = parse_fqdn(session, host)
            except AquilonError, err:
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
                            (host, existing.hardware_entity.interfaces[0].mac,
                             mac)
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
                        "machine." % \
                        (host, mac, dbinterface.hardware_entity.label)
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
                        "%s is already tied to %s." % \
                        (host, mac, dbmachine.fqdn)
                failed.append(msg)
                logger.info(msg)
                continue
            dbhost = Host(machine=dbmachine, branch=dbdomain,
                          status=dbstatus, owner_grn=dbpersonality.owner_grn,
                          personality=dbpersonality, operating_system=dbos,
                          comments="Created by refresh_windows_host")
            session.add(dbhost)
            dbhost.grns.append(dbpersonality.owner_grn)
            dbfqdn = Fqdn.get_or_create(session, name=short,
                                        dns_domain=dbdns_domain, preclude=True)
            dbdns_rec = ReservedName(fqdn=dbfqdn)
            session.add(dbdns_rec)
            dbmachine.primary_name = dbdns_rec
            success.append("Added host entry for %s (%s)." %
                           (dbmachine.label, dbdns_rec.fqdn))
            if dbmachine.vm_container:
                containers.add(dbmachine.vm_container)
            session.flush()

        session.flush()
        if failed:
            raise PartialError(success, failed)

        return
