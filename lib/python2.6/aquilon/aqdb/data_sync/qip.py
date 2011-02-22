# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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
""" Routines to query information from QIP """

from ipaddr import (IPv4Address, IPv4Network, AddressValueError,
                    NetmaskValueError)

from aquilon.exceptions_ import PartialError, ArgumentError
from aquilon.aqdb.model import (Network, NetworkEnvironment, RouterAddress,
                                ARecord, Building, DnsEnvironment)

from sqlalchemy.orm import subqueryload, defer, contains_eager


class QIPRefresh(object):
    def __init__(self, session, logger, dbbuilding, dryrun, incremental):
        self.session = session
        self.logger = logger
        self.building = dbbuilding
        self.dryrun = dryrun
        self.incremental = incremental

        # Synchronize the internal environment only
        self.net_env = NetworkEnvironment.get_unique_or_default(session)

        self.errors = []

        self.dns_env = DnsEnvironment.get_unique_or_default(session)

        # Cache building information. Load all buildings even if we're
        # interested in only one, so we can verify subnetdata.txt
        self.buildings = {}
        q = session.query(Building)
        for item in q:
            self.buildings[item.name] = item

        # Used to limit the number of warnings
        self.unknown_syslocs = set()

        # Load existing networks
        self.aqnetworks = {}
        q = session.query(Network)
        q = q.filter_by(network_environment=self.net_env)
        if dbbuilding:
            q = q.filter_by(location=dbbuilding)
        q = q.options(subqueryload("routers"))
        for item in q:
            self.aqnetworks[item.ip] = item

        # Save how many networks we had initially
        self.networks_before = len(self.aqnetworks.keys())

    def error(self, msg):
        self.logger.error(msg)
        self.errors.append(msg)

    def commit_if_needed(self, msg):
        self.logger.client_info(msg)
        try:
            if self.dryrun:
                self.session.flush()
            if self.incremental:
                self.session.commit()
        except Exception, err:
            self.error(err)
            self.session.rollback()

    def refresh_system_networks(self):
        q = self.session.query(ARecord)
        q = q.join(Network)
        q = q.options(contains_eager('network'))
        q = q.filter_by(network_environment=self.net_env)
        q = q.order_by(ARecord.ip)
        systems = q.all()

        q = self.session.query(Network)
        q = q.filter_by(network_environment=self.net_env)
        q = q.options(defer('location_id'))
        q = q.options(defer('side'))
        q = q.options(defer('is_discoverable'))
        q = q.options(defer('is_discovered'))
        q = q.order_by(Network.ip)
        networks = q.all()

        def set_network(dnsrec, net):
            if dnsrec.network != net:
                dnsrec.network = net
                self.commit_if_needed('Updating %s [%s] with network %s' %
                                      (dnsrec.fqdn, dnsrec.ip, net.ip))

        s_index = 0
        n_index = 0
        # Iterate through the ordered lists matching systems to their networks.
        # Not worried about the edge cases of no networks or no systems.  If
        # there are no systems there is nothing to fix.  If there are no
        # networks then all the systems are pointing at null anyway.
        while (s_index < len(systems) and n_index < len(networks)):
            # database objects
            sys = systems[s_index]
            net = networks[n_index]

            # Hopefully the common case... our system IP is in the range
            # of the current network.  Make sure the network is set
            # appropriately and move on to the next system.
            if sys.ip in net.network:
                set_network(sys, net)
                s_index += 1
                continue

            # Our system is beyond the range of the current network, so
            # proceed to checking against the next network.
            if sys.ip > net.broadcast:
                n_index += 1
                continue

            # At this point we know our system is not in the range of
            # any networks.  We started at the "lowest" network and
            # have been working up.  Since the system IP is less than
            # the network IP we can't expect incrementing to the next
            # network to help us find one. :)
            self.error('No network found for IP address %s [%s].' %
                       (sys.ip, sys.fqdn))
            set_network(sys, None)
            s_index += 1
            continue

    def parse_line(self, line):
        """
        Parses a line from subnetdata.txt

        Returns None if the line did not contain network information. Otherwise
        it returns the attributes that are interesting to us as a dict.
        """

        # Format of subnetdata.txt:
        # - Fields are separated by tabs
        # - A field is a key/value pair, separated by a space
        # - The value of the DefaultRouters field is a comma-separated list of
        #   IP addresses
        # - The value of the UDF field is a list of "<key>=<value>" pairs,
        #   separated by ';'

        qipinfo = {}

        name = None
        location = None
        network_type = "unknown"
        side = "a"
        routers = []

        fields = line.split("\t")
        for field in fields:
            # The value may contain embedded spaces
            (key, value) = field.split(" ", 1)

            # Some fields contain structured data
            if key == "UDF":
                udf = {}
                for item in value.split(";"):
                    (udfkey, udfvalue) = item.split("=", 1)
                    udf[udfkey] = udfvalue
                value = udf

            qipinfo[key] = value

        # Sanity check
        if "SubnetId" not in qipinfo or "SubnetAddress" not in qipinfo or \
           "SubnetMask" not in qipinfo:
            self.logger.info("WARNING: Line contains no network: %s" % line)
            return None

        if "SubnetName" in qipinfo:
            name = qipinfo["SubnetName"].strip().lower()
        if not name:
            name = qipinfo["SubnetAddress"]

        # Parse the network address/netmask
        try:
            address = IPv4Network("%s/%s" % (qipinfo["SubnetAddress"],
                                             qipinfo["SubnetMask"]))
        except AddressValueError:
            raise ValueError("Failed to parse the network address")
        except NetmaskValueError:
            raise ValueError("Failed to parse the netmask")

        # Parse the list of routers
        if "DefaultRouters" in qipinfo:
            for addr in qipinfo["DefaultRouters"].split(","):
                try:
                    routers.append(IPv4Address(addr))
                except AddressValueError:
                    raise ValueError("Bad IP address in DefaultRouters")

        # Extract MS-specific information from the UDF field
        if "UDF" in qipinfo:
            if "LOCATION" in qipinfo["UDF"]:
                # Values in QIP sometimes contain spaces and mixed case
                syslocstr = qipinfo["UDF"]["LOCATION"].strip().lower()
                sysloc = syslocstr.split('.')
                if len(sysloc) >= 3:
                    if sysloc[-3] in self.buildings:
                        location = self.buildings[sysloc[-3]]
                    else:
                        # Do not make "refresh network --all" fail if a new
                        # building does not exist in AQDB yet. Warn once for
                        # every unknown sysloc we encounter.
                        if syslocstr in self.unknown_syslocs:
                            return None
                        self.unknown_syslocs.add(syslocstr)
                        self.logger.client_info("Unknown building code in sysloc "
                                                "%s, ignoring" % syslocstr)
                        return None
                else:
                    raise ValueError("Failed to parse LOCATION")

            if "TYPE" in qipinfo["UDF"]:
                network_type = qipinfo["UDF"]["TYPE"].strip().lower()

            if "SIDE" in qipinfo["UDF"]:
                side = qipinfo["UDF"]["SIDE"].strip().lower()

        # FIXME: How to handle networks with no location? dsdb maps them to
        # sysloc "xx.ny.na", so mimic that for now
        if not location:
            if "xx" in self.buildings:
                location = self.buildings["xx"]
            else:
                # FIXME: the testsuite does not have the "xx" building
                return None

        return {"name": name,
                "address": address,
                "location": location,
                "type": network_type,
                "side": side,
                "routers": routers}

    def update_network(self, dbnetwork, qipinfo):
        if dbnetwork.name != qipinfo["name"]:
            oldname = dbnetwork.name
            dbnetwork.name = qipinfo["name"]
            self.commit_if_needed("Setting network %s name to %s" %
                                  (oldname, dbnetwork.name))
        if dbnetwork.network_type != qipinfo["type"]:
            dbnetwork.network_type = qipinfo["type"]
            self.commit_if_needed("Setting {0:l} type to "
                                  "{1}".format(dbnetwork, qipinfo["type"]))
        if dbnetwork.location != qipinfo["location"]:
            dbnetwork.location = qipinfo["location"]
            self.commit_if_needed("Setting {0:l} location to "
                                  "{1:l}".format(dbnetwork, qipinfo["location"]))
        if dbnetwork.side != qipinfo["side"]:
            dbnetwork.side = qipinfo["side"]
            self.commit_if_needed("Setting {0:l} side to "
                                  "{1}".format(dbnetwork, qipinfo["side"]))
        if dbnetwork.netmask != qipinfo["address"].netmask:
            dbnetwork.cidr = qipinfo["address"].prefixlen
            self.commit_if_needed("Setting {0:l} netmask to "
                                  "{1}".format(dbnetwork,
                                               qipinfo["address"].netmask))

        old_rtrs = set(dbnetwork.router_ips)
        new_rtrs = set(qipinfo["routers"])

        for ip in old_rtrs - new_rtrs:
            dbnetwork.router_ips.remove(ip)
            self.commit_if_needed("Removing router {0:s} from "
                                  "{1:l}".format(ip, dbnetwork))

        for ip in new_rtrs - old_rtrs:
            dbnetwork.routers.append(RouterAddress(ip=ip,
                                                   dns_environment=self.dns_env))
            self.commit_if_needed("Adding router {0:s} to "
                                  "{1:l}".format(ip, dbnetwork))

        # TODO: add support for updating router locations

    def refresh(self, filehandle):
        linecnt = 0
        qipnetworks = {}
        for line in filehandle:
            linecnt += 1
            line = line.rstrip("\n")
            try:
                qipinfo = self.parse_line(line)
                if not qipinfo:
                    continue
                if self.building and qipinfo["location"] != self.building:
                    continue
                qipnetworks[qipinfo["address"].ip] = qipinfo
            except ValueError, err:
                self.error("%s; skipping line %d: %s" % (err, linecnt, line))

        deletes = set(self.aqnetworks.keys()) - set(qipnetworks.keys())
        # Safety margin: refuse if we're about to delete more than 1/4 of the
        # existing networks
        if len(deletes) > self.networks_before / 4:
            # TODO: add a --force argument
            raise ArgumentError("The operation would delete more than 25% of "
                                "the networks defined in AQDB, refusing.")
        for ip in deletes:
            self.session.delete(self.aqnetworks[ip])
            self.commit_if_needed("Deleting {0:l}".format(self.aqnetworks[ip]))
            del self.aqnetworks[ip]
        self.session.flush()

        # What remained in self.aqnetworks is also in qipnetworks, so check for
        # updates
        for ip, dbnetwork in self.aqnetworks.items():
            self.update_network(dbnetwork, qipnetworks[ip])
            del qipnetworks[ip]
        self.session.flush()

        # What remained in qipnetworks was not present in AQDB
        for qipinfo in qipnetworks.values():
            dbnetwork = Network(name=qipinfo["name"], network=qipinfo["address"],
                                network_type=qipinfo["type"], side=qipinfo["side"],
                                location=qipinfo["location"],
                                network_environment=self.net_env)
            self.session.add(dbnetwork)
            self.commit_if_needed("Adding {0:l}".format(dbnetwork))
            for ip in qipinfo["routers"]:
                dbnetwork.routers.append(RouterAddress(ip=ip,
                                                       dns_environment=self.dns_env))
                self.commit_if_needed("Adding router {0:s} to "
                                      "{1:l}".format(ip, dbnetwork))
        self.session.flush()

        self.refresh_system_networks()

        if self.errors:
            if self.incremental:
                msg = ""
            else:
                msg = "No changes applied because of errors."
            raise PartialError(success=[], failed=self.errors, success_msg=msg)

