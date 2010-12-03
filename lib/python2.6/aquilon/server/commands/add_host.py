# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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


from aquilon.exceptions_ import (ArgumentError, ProcessException, AquilonError,
                                 InternalError)
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.branch import get_branch_and_author
from aquilon.server.dbwrappers.hardware_entity import parse_primary_name
from aquilon.server.dbwrappers.interface import generate_ip
from aquilon.aqdb.model import (Domain, Host, OperatingSystem, Archetype,
                                HostLifecycle, Machine, Personality)
from aquilon.server.templates.base import PlenaryCollection
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.templates.cluster import PlenaryCluster
from aquilon.server.locks import lock_queue
from aquilon.server.processes import DSDBRunner


class CommandAddHost(BrokerCommand):

    required_parameters = ["hostname", "machine", "archetype"]

    def render(self, session, logger, hostname, machine, archetype, domain,
               sandbox, osname, osversion, buildstatus, personality, comments,
               zebra_interfaces, skip_dsdb_check=False, **arguments):
        (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                     domain=domain,
                                                     sandbox=sandbox,
                                                     compel=True)
        if not buildstatus:
            buildstatus = 'build'
        dbstatus = HostLifecycle.get_unique(session, buildstatus, compel=True)
        dbmachine = Machine.get_unique(session, machine, compel=True)

        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        if not personality:
            if dbarchetype.name == 'aquilon':
                personality = 'inventory'
            else:
                personality = 'generic'
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)

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
                raise ArgumentError("Can not determine a sensible default OS "
                                    "for archetype %s. Please use the "
                                    "--osname and --osversion parameters." %
                                    (dbarchetype.name))

        dbos = OperatingSystem.get_unique(session, name=osname,
                                          version=osversion,
                                          archetype=dbarchetype, compel=True)

        if (dbmachine.model.machine_type == 'aurora_node' and
                dbpersonality.archetype.name != 'aurora'):
            raise ArgumentError("Machines of type aurora_node can only be "
                                "added with archetype aurora.")

        session.refresh(dbmachine)
        if dbmachine.host:
            raise ArgumentError("{0:c} {0.label} is already allocated to "
                                "{1:l}.".format(dbmachine, dbmachine.host))

        if zebra_interfaces:
            self.assign_zebra_address(session, dbmachine, hostname,
                                      zebra_interfaces, **arguments)
        else:
            self.assign_normal_address(session, dbmachine, hostname,
                                       **arguments)

        dbhost = Host(machine=dbmachine, branch=dbbranch,
                      sandbox_author=dbauthor, personality=dbpersonality,
                      status=dbstatus, operating_system=dbos, comments=comments)
        session.add(dbhost)
        session.flush()
        session.refresh(dbhost)

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(PlenaryMachineInfo(dbmachine, logger=logger))
        if dbmachine.cluster:
            plenaries.append(PlenaryCluster(dbmachine.cluster, logger=logger))

        key = plenaries.get_write_key()
        try:
            lock_queue.acquire(key)
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
                        raise ArgumentError("Could not find host in DSDB: %s" % e)
            elif not dbmachine.primary_ip:
                logger.info("No IP for %s, not adding to DSDB." % dbmachine.fqdn)
            else:
                try:
                    dsdb_runner.update_host(dbmachine, None)
                except AquilonError, err:
                    raise ArgumentError("Could not add host to DSDB: %s" % err)
        except:
            plenaries.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        return

    def assign_normal_address(self, session, dbmachine, hostname, **arguments):
        """ Assign an IP address to the boot interface """

        dbinterface = None
        # Look up the boot interface
        for iface in dbmachine.interfaces:
            if iface.bootable:
                dbinterface = iface
                # If the boot interface is enslaved in a bonding/bridge setup,
                # then assign the address to the master instead
                while dbinterface.master:
                    dbinterface = dbinterface.master
                break

        # This method is allowed to return None. This can only happen
        # (currently) using add_aurora_host, add_windows_host, or possibly by
        # bypassing the aq client and posting a request directly.
        ip = generate_ip(session, dbinterface, **arguments)

        # FIXME: This should be in generic code, but parse_primary_name()
        # currently has to be called after the IP have been generated but
        # before the AddressAssignment record is created
        dbdns_rec = parse_primary_name(session, hostname, ip)
        dbmachine.primary_name = dbdns_rec

        if ip:
            if not dbinterface:
                raise ArgumentError("You have specified an IP address for the "
                                    "host, but {0:l} does not have a bootable "
                                    "interface.".format(dbmachine))
            if ip not in dbinterface.addresses:
                for addr in dbinterface.assignments:
                    if not addr.label:
                        raise ArgumentError("{0} already has an unlabeled IP "
                                            "address.".format(dbinterface))
                dbinterface.addresses.append(ip)

    def assign_zebra_address(self, session, dbmachine, hostname,
                             zebra_interfaces, **arguments):
        """ Assign a Zebra-managed address to multiple interfaces """

        # --autoip does not make sense with Zebra, so no need to pass an
        # interface
        ip = generate_ip(session, None, **arguments)
        if ip is None:
            raise ArgumentError("Zebra configuration requires an IP address.")

        # FIXME: This should be in generic code, but parse_primary_name()
        # currently has to be called after the IP have been generated but before
        # the AddressAssignment records are created
        dbdns_rec = parse_primary_name(session, hostname, ip)
        dbmachine.primary_name = dbdns_rec

        for name in zebra_interfaces.split(","):
            dbinterface = None
            for iface in dbmachine.interfaces:
                if iface.name == name:
                    dbinterface = iface
                    # If the interface is enslaved in a bonding/bridge setup,
                    # then assign the address to the master instead
                    while dbinterface.master:
                        dbinterface = dbinterface.master
                    break
            if not dbinterface:
                raise ArgumentError("{0} does not have an interface named "
                                    "{1}.".format(dbmachine, name))
            for addr in dbinterface.assignments:
                if addr.label == "hostname":
                    raise ArgumentError("{0} already has an alias named "
                                        "hostname.".format(dbinterface))
            dbinterface.addresses.append({"ip": ip,
                                          "label": "hostname",
                                          "usage": "zebra"})
