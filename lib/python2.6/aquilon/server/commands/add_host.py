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


from aquilon.exceptions_ import ArgumentError, ProcessException
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
               skip_dsdb_check=False, **arguments):
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

        dbinterface = None
        if dbpersonality.archetype.name != 'aurora':
            for interface in dbmachine.interfaces:
                if interface.interface_type != 'public':
                    continue
                if interface.bootable:
                    if dbinterface:
                        # FIXME: Is this actually a problem?
                        raise ArgumentError("Multiple public interfaces on "
                                            "machine %s are marked bootable." %
                                            machine)
                    dbinterface = interface

        # This method is allowed to return None, which will pass through
        # the next two.
        # This can only happen (currently) using add_aurora_host,
        # add_windows_host, or possibly by bypassing the aq client and
        # posting a request directly.
        ip = generate_ip(session, dbinterface, **arguments)
        dbdns_rec = parse_primary_name(session, hostname, ip)

        dbhost = Host(machine=dbmachine, branch=dbbranch,
                      sandbox_author=dbauthor, personality=dbpersonality,
                      status=dbstatus, operating_system=dbos, comments=comments)
        session.add(dbhost)
        dbmachine.primary_name = dbdns_rec
        if ip and dbinterface and ip not in dbinterface.vlans[0].addresses:
            dbinterface.vlans[0].addresses.append(ip)
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
                # For anything else, reserve the name and IP in DSDB.
                try:
                    args = [dbmachine.fqdn, dbmachine.primary_ip]
                    if dbinterface:
                        args.extend([dbinterface.name, dbinterface.mac])
                    else:
                        args.extend([None, None])
                    dsdb_runner.add_host_details(*args)
                except ProcessException, e:
                    raise ArgumentError("Could not add host to DSDB: %s" % e)
        except:
            plenaries.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        return
