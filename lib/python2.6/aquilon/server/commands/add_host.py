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
"""Contains the logic for `aq add host`."""


from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.domain import verify_domain
from aquilon.server.dbwrappers.status import get_status
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.server.dbwrappers.system import parse_system_and_verify_free
from aquilon.server.dbwrappers.interface import (generate_ip,
                                                 restrict_tor_offsets)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.aqdb.model import Host, OperatingSystem
from aquilon.server.templates.base import (compileLock, compileRelease,
                                           PlenaryCollection)
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.templates.cluster import PlenaryCluster
from aquilon.server.processes import DSDBRunner


class CommandAddHost(BrokerCommand):

    required_parameters = ["hostname", "machine", "archetype", "domain"]

    def render(self, session, logger, hostname, machine, archetype,
               personality, domain, buildstatus, comments, osname, osversion,
               skip_dsdb_check=False, **arguments):
        dbdomain = verify_domain(session, domain,
                self.config.get("broker", "servername"))
        if buildstatus:
            dbstatus = get_status(session, buildstatus)
        else:
            dbstatus = get_status(session, "build")
        dbmachine = get_machine(session, machine)

        dbarchetype = get_archetype(session, archetype)
        if not personality:
            if dbarchetype.name == 'aquilon':
                personality = 'inventory'
            else:
                personality = 'generic'
        dbpersonality = get_personality(session, archetype, personality)

        if dbarchetype.name == 'aquilon':
            # default to os linux/4.0.1-x86_64 for aquilon
            # this is a statistically valid assumption given the population
            # of aquilon machines as of Oct. 2009
            if not osname:
                osname = 'linux'
            if not osversion:
                osversion = '4.0.1-x86_64'
        elif dbarchetype.name =='aurora':
            if not osname:
                #no solaris yet
                osname = 'linux'
            if not osversion:
                osversion = 'generic'
        elif dbarchetype.name == 'windows':
            if not osname:
                osname = 'windows'
            if not osversion:
                osversion = 'generic'
        else:
            if not osname or not osversion:
                raise ArgumentError("Can not determine a sensible default OS for archetype %s. Please use osname and osversion parameters" % (dbarchetype.name))

        dbos = OperatingSystem.get_unique(session, name=osname,
                                          version=osversion,
                                          archetype=dbarchetype, compel=True)

        if (dbmachine.model.machine_type == 'aurora_node' and
                dbpersonality.archetype.name != 'aurora'):
            raise ArgumentError("Machines of aurora_node can only be added with archetype aurora")

        session.refresh(dbmachine)
        if dbmachine.host:
            raise ArgumentError("Machine '%s' is already allocated to host '%s'." %
                    (dbmachine.name, dbmachine.host.fqdn))

        (short, dbdns_domain) = parse_system_and_verify_free(session, hostname)

        dbinterface = None
        mac = None
        if dbpersonality.archetype.name != 'aurora':
            # Any host being added to DSDB will need a valid primary interface.
            # XXX: This check for msad is horrible... look to get rid of it
            # when system and interface tables are restructured.
            if not dbmachine.interfaces and dbdns_domain.name != 'msad.ms.com':
                raise ArgumentError("Machine '%s' has no interfaces." % machine)
            for interface in dbmachine.interfaces:
                if interface.interface_type != 'public':
                    continue
                if interface.bootable:
                    if dbinterface:
                        # FIXME: Is this actually a problem?
                        raise ArgumentError("Multiple public interfaces on machine '%s' are marked bootable" % machine)
                    dbinterface = interface
            if dbinterface:
                mac = dbinterface.mac
            # XXX: Another horrible check here...
            if not dbinterface and dbdns_domain.name != 'msad.ms.com':
                raise ArgumentError("Machine '%s' requires a bootable interface." % machine)

        # This method is allowed to return None, which will pass through
        # the next two.
        ip = generate_ip(session, dbinterface, **arguments)
        dbnetwork = get_net_id_from_ip(session, ip)
        restrict_tor_offsets(dbnetwork, ip)

        dbhost = Host(machine=dbmachine, domain=dbdomain, status=dbstatus,
                      mac=mac, ip=ip, network=dbnetwork, operating_system=dbos,
                      name=short, dns_domain=dbdns_domain,
                      personality=dbpersonality, comments=comments)
        session.add(dbhost)
        if dbinterface:
            dbinterface.system = dbhost
            session.add(dbinterface)
        session.flush()
        session.refresh(dbhost)

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(PlenaryMachineInfo(dbmachine, logger=logger))
        if dbmachine.cluster:
            plenaries.append(PlenaryCluster(dbmachine.cluster, logger=logger))

        try:
            compileLock(logger=logger)
            plenaries.write(locked=True)

            # XXX: This (and some of the code above) is horrible.  There
            # should be a generic/configurable hook here that could kick
            # in based on archetype and/or domain.
            dsdb_runner = DSDBRunner(logger=logger)
            if dbhost.archetype.name == 'aurora':
                # For aurora, check that DSDB has a record of the host.
                if not skip_dsdb_check:
                    try:
                        fields = dsdb_runner.show_host(hostname)
                    except ProcessException, e:
                        raise ArgumentError("Could not find host in dsdb: %s" % e)
            elif dbdns_domain.name == 'msad.ms.com':
                # We should probably check that the host is valid in the
                # appropriate system...
                pass
            else:
                # For anything else, reserve the name and IP in DSDB.
                try:
                    dsdb_runner.add_host(dbinterface)
                except ProcessException, e:
                    raise ArgumentError("Could not add host to dsdb: %s" % e)
        except:
            plenaries.restore_stash()
            raise
        finally:
            compileRelease(logger=logger)

        return
