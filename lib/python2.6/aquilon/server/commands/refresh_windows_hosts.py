# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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

from aquilon.exceptions_ import PartialError, InternalError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import get_host_dependencies
from aquilon.server.templates.base import PlenaryCollection
from aquilon.server.templates.cluster import PlenaryCluster
from aquilon.server.locks import lock_queue, SyncKey
from aquilon.aqdb.model import (Host, Interface, Machine, Domain, Archetype,
                                Personality, HostLifecycle, DnsDomain, System,
                                OperatingSystem, ReservedName)


class CommandRefreshWindowsHosts(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, dryrun, **arguments):
        clusters = set()
        key = SyncKey(data="windows", logger=logger)
        lock_queue.acquire(key)
        partial_error = None
        try:
            try:
                self.refresh_windows_hosts(session, logger, clusters)
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
        finally:
            lock_queue.release(key)
        if clusters:
            plenaries = PlenaryCollection(logger=logger)
            for dbcluster in clusters:
                plenaries.append(PlenaryCluster(dbcluster, logger=logger))
            plenaries.write()
        if partial_error:
            raise partial_error
        return

    def refresh_windows_hosts(self, session, logger, clusters):
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
            if dbmachine.cluster:
                clusters.add(dbmachine.cluster)
            session.delete(dbhost)
            session.delete(dbmachine.primary_name)
            session.expire(dbmachine, ['_primary_name_asc'])
        session.flush()
        # The Host() creations below fail when autoflush is enabled.
        session.autoflush = False

        dbdomain = Domain.get_unique(session,
                                     self.config.get("broker",
                                                     "windows_host_domain"),
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
            if host.find('.') < 0:
                msg = "Skipping host %s: Missing DNS domain in name." % \
                        host
                failed.append(msg)
                logger.info(msg)
                continue
            (short, dns_domain) = host.split('.', 1)
            dbdns_domain = DnsDomain.get_unique(session, dns_domain)
            if not dbdns_domain:
                msg = "Skipping host %s: No AQDB entry for DNS domain %s." % \
                        (host, dns_domain)
                failed.append(msg)
                logger.info(msg)
                continue
            existing = System.get_unique(session, name=short,
                                         dns_domain=dbdns_domain)
            if existing:
                if not existing.hardware_entity:
                    msg = "Skipping host %s: It is not a primary name." % host
                    failed.append(msg)
                    logger.info(msg)
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
            if dbinterface.vlans[0].assignments:
                msg = "Skipping host %s: The AQDB interface with MAC address " \
                        "%s is already tied to %s." % \
                        (host, mac, dbinterface.vlans[0].assignments[0].fqdns[0])
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
                          status=dbstatus,
                          personality=dbpersonality, operating_system=dbos,
                          comments="Created by refresh_windows_host")
            session.add(dbhost)
            dbdns_rec = ReservedName(name=short, dns_domain=dbdns_domain)
            session.add(dbdns_rec)
            dbmachine.primary_name = dbdns_rec
            success.append("Added host entry for %s (%s)." %
                           (dbmachine.label, dbdns_rec.fqdn))
            if dbmachine.cluster:
                clusters.add(dbmachine.cluster)
            session.flush()

        session.flush()
        if failed:
            raise PartialError(success, failed)

        return
