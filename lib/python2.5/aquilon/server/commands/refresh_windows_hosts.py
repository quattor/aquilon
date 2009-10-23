# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
"""Contains the logic for `aq refresh network`."""


from threading import Lock
import sqlite3

from aquilon.exceptions_ import PartialError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import get_host_dependencies
from aquilon.aqdb.model import (Host, Interface, Machine, Domain, Archetype,
                                Personality, Status, DnsDomain, System)


REFRESH_WINDOWS_HOSTS_LOCK = Lock()


class CommandRefreshNetwork(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, dryrun, **arguments):
        logger.client_info("Acquiring lock to refresh windows hosts")
        REFRESH_WINDOWS_HOSTS_LOCK.acquire()
        logger.client_info("Acquired lock to refresh windows hosts")
        try:
            self.refresh_windows_hosts(session, logger)
            if dryrun:
                session.rollback()
        except PartialError, e:
            if not dryrun:
                # Commit whatever was successful, since the session would
                # normally be rolled back on error.
                session.commit()
            raise e
        finally:
            logger.client_info("Released lock from refresh windows hosts.")
            REFRESH_WINDOWS_HOSTS_LOCK.release()
        return

    def refresh_windows_hosts(self, session, logger):
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
            if dbhost.fqdn in windows_hosts and \
               dbhost.mac == windows_hosts[dbhost.fqdn]:
                # All is well
                continue
            deps = get_host_dependencies(session, dbhost)
            if deps:
                msg = "Skipping removal of host %s with dependencies: %s" % \
                        (dbhost.fqdn, ", ".join(deps))
                failed.append(msg)
                logger.info(msg)
                continue
            for dbinterface in dbhost.interfaces:
                # Verify that there's only one?
                dbinterface.system = None
                session.add(dbinterface)
            success.append("Removed host entry for %s (%s)" %
                           (dbhost.machine.name, dbhost.fqdn))
            session.delete(dbhost)
        session.flush()
        # The Host() creations below fail when autoflush is enabled.
        session.autoflush = False

        dbdomain = Domain.get_unique(session,
                                     self.config.get("broker",
                                                     "windows_host_domain"))
        dbarchetype = Archetype.get_unique(session, "windows")
        dbpersonality = Personality.get_unique(session, archetype=dbarchetype,
                                               name="generic")
        dbstatus = Status.get_unique(session, "ready")
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
                msg = "Skipping host %s: No AQDB entry for DNS domain '%s'" % \
                        (host, dns_domain)
                failed.append(msg)
                logger.info(msg)
                continue
            existing = System.get_unique(session, name=short,
                                         dns_domain=dbdns_domain)
            if existing:
                # If these are invalid there should have been a deletion
                # attempt above.
                if not existing.interfaces:
                    msg = "Skipping host %s: Host already exists but has " % \
                            "no interface attached." % host
                    failed.append(msg)
                    logger.info(msg)
                elif existing.interfaces[0].mac != mac:
                    msg = "Skipping host %s: Host already exists but with " \
                            "MAC %s and not MAC %s" % \
                            (host, existing.interfaces[0].mac, mac)
                    failed.append(msg)
                    logger.info(msg)
                continue
            dbinterface = session.query(Interface).filter_by(mac=mac).first()
            if not dbinterface:
                msg = "Skipping host %s: MAC %s is not present in AQDB" % \
                        (host, mac)
                failed.append(msg)
                logger.info(msg)
                continue
            q = session.query(Machine)
            q = q.filter_by(id=dbinterface.hardware_entity.id)
            dbmachine = q.first()
            if not dbmachine:
                msg = "Skipping host %s: the AQDB interface with mac %s is " \
                        "tied to hardware %s instead of a virtual machine" % \
                        (host, mac, dbinterface.hardware_entity.hardware_name)
                failed.append(msg)
                logger.info(msg)
                continue
            if dbinterface.system:
                msg = "Skipping host %s: the AQDB interface with mac %s is " \
                        "already tied to %s" % \
                        (host, mac, dbinterface.system.fqdn)
                failed.append(msg)
                logger.info(msg)
                continue
            dbhost = Host(machine=dbmachine, domain=dbdomain,
                          status=dbstatus, mac=mac, ip=None, network=None,
                          name=short, dns_domain=dbdns_domain,
                          personality=dbpersonality,
                          comments="Created by refresh_windows_host")
            session.add(dbhost)
            dbinterface.system = dbhost
            session.add(dbinterface)
            success.append("Added host entry for %s (%s)" %
                           (dbhost.machine.name, dbhost.fqdn))
            session.flush()

        session.flush()
        if failed:
            raise PartialError(success, failed)

        return


