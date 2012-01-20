# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011,2012  Contributor
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
import heapq

from aquilon.exceptions_ import PartialError, ArgumentError
from aquilon.aqdb.model import (NetworkEnvironment, Network, RouterAddress,
                                ARecord, DnsEnvironment, AddressAssignment,
                                Building)
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.dbwrappers.network import fix_foreign_links

from sqlalchemy.orm import subqueryload, lazyload, defer, contains_eager
from sqlalchemy.sql import update, and_, or_


# Add a wrapper around heapq.heappop because handling None is simpler than
# adding try/except blocks everywhere
def heap_pop(heap):
    try:
        return heapq.heappop(heap)
    except IndexError:
        return None


class QIPInfo(object):
    def __init__(self, name, address, location, network_type, side, routers):
        self.name = name
        self.address = address
        self.location = location
        self.network_type = network_type
        self.side = side
        self.routers = routers

    def __cmp__(self, other):
        # The refresh algorithm depends on QIPInfo objects being ordered by the
        # network IP address
        return cmp(self.address.ip, other.address.ip)


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

        # Load existing networks. We have to load all, otherwise we won't be
        # able to fix networks with wrong location
        self.aqnetworks = {}
        q = session.query(Network)
        q = q.filter_by(network_environment=self.net_env)
        q = q.options(subqueryload("routers"))
        for item in q:
            self.aqnetworks[item.ip] = item

        # Save how many networks we had initially
        self.networks_before = len(self.aqnetworks.keys())

    def error(self, msg):
        self.logger.error(msg)
        self.errors.append(msg)

    def commit_if_needed(self):
        try:
            if self.dryrun:
                self.session.flush()
            if self.incremental:
                self.session.commit()
        except Exception, err:  # pragma: no cover
            self.error(str(err))
            self.session.rollback()

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

        return QIPInfo(name=name, address=address, location=location,
                       network_type=network_type, side=side, routers=routers)

    def update_network(self, dbnetwork, qipinfo):
        """ Update the network parameters except the netmask """

        if dbnetwork.name != qipinfo.name:
            self.logger.client_info("Setting network {0:a} name to {1}"
                                    .format(dbnetwork, qipinfo.name))
            oldname = dbnetwork.name
            dbnetwork.name = qipinfo.name
        if dbnetwork.network_type != qipinfo.network_type:
            self.logger.client_info("Setting network {0:a} type to {1}"
                                    .format(dbnetwork, qipinfo.network_type))
            dbnetwork.network_type = qipinfo.network_type
        if dbnetwork.location != qipinfo.location:
            self.logger.client_info("Setting network {0:a} location to {1:l}"
                                    .format(dbnetwork, qipinfo.location))
            dbnetwork.location = qipinfo.location
        if dbnetwork.side != qipinfo.side:
            self.logger.client_info("Setting network {0:a} side to {1}"
                                    .format(dbnetwork, qipinfo.side))
            dbnetwork.side = qipinfo.side

        old_rtrs = set(dbnetwork.router_ips)
        new_rtrs = set(qipinfo.routers)

        del_routers = []
        for router in dbnetwork.routers:
            if router.ip in old_rtrs - new_rtrs:
                del_routers.append(router)

        for router in del_routers:
            self.logger.client_info("Removing router {0:s} from "
                                    "{1:l}".format(router.ip, dbnetwork))
            map(delete_dns_record, router.dns_records)
            dbnetwork.routers.remove(router)

        for ip in new_rtrs - old_rtrs:
            self.add_router(dbnetwork, ip)

        # TODO: add support for updating router locations

        return dbnetwork.netmask == qipinfo.address.netmask

    def add_network(self, qipinfo):
        dbnetwork = Network(name=qipinfo.name, network=qipinfo.address,
                            network_type=qipinfo.network_type,
                            side=qipinfo.side, location=qipinfo.location,
                            network_environment=self.net_env)
        self.session.add(dbnetwork)
        self.logger.client_info("Adding network {0:a}".format(dbnetwork))
        for ip in qipinfo.routers:
            self.add_router(dbnetwork, ip)
        self.session.flush()
        return dbnetwork

    def del_network(self, dbnetwork):
        # Check if the network is in use and a return readable error message if
        # it is
        in_use = False
        for addr in dbnetwork.assignments:
            self.error("{0} cannot be deleted because {1} is still assigned to "
                       "{2:l}.".format(dbnetwork, addr.ip, addr.interface))
            in_use = True
        for dns_rec in dbnetwork.dns_records:
            if hasattr(dns_rec, "ip") and dns_rec.ip in dbnetwork.router_ips:
                continue
            self.error("{0} cannot be deleted because DNS record {1:a} still "
                       "exists.".format(dbnetwork, dns_rec))
            in_use = True

        if not in_use:
            for router in dbnetwork.routers:
                self.logger.client_info("Removing router {0:s} from "
                                        "{1:l}".format(router.ip, dbnetwork))
                map(delete_dns_record, router.dns_records)
            dbnetwork.routers = []
            self.logger.client_info("Deleting network {0:a}".format(dbnetwork))
            self.session.delete(dbnetwork)

    def add_router(self, dbnetwork, ip):
        dbnetwork.routers.append(RouterAddress(ip=ip,
                                               dns_environment=self.dns_env))
        self.logger.client_info("Adding router {0:s} to "
                                "{1:l}".format(ip, dbnetwork))

    def check_split_network(self, dbnetwork):
        # If a network was split and some of the subnets were deleted, then
        # some IP address allocations may be left in limbo. Force these cases to
        # generate an SQL error by violating the NOT NULL constraint
        self.session.execute(
            update(AddressAssignment.__table__,
                   values={'network_id': None})
            .where(and_(AddressAssignment.network_id == dbnetwork.id,
                        or_(AddressAssignment.ip < dbnetwork.ip,
                            AddressAssignment.ip > dbnetwork.broadcast)))
        )

        self.session.execute(
            update(ARecord.__table__,
                   values={'network_id': None})
            .where(and_(ARecord.network_id == dbnetwork.id,
                        or_(ARecord.ip < dbnetwork.ip,
                            ARecord.ip > dbnetwork.broadcast)))
        )

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
                if self.building and qipinfo.location != self.building:
                    continue
                qipnetworks[qipinfo.address.ip] = qipinfo
            except ValueError, err:
                self.error("%s; skipping line %d: %s" % (err, linecnt, line))

        # Check/update network attributes that do not affect other objects. Do
        # this in a single transaction, even in incremental mode
        ips = self.aqnetworks.keys()
        for ip in ips:
            if ip not in qipnetworks:
                # "Forget" networks not inside the requested building to prevent
                # them being deleted
                if self.building and self.aqnetworks[ip].location != self.building:
                    del self.aqnetworks[ip]
                continue
            if self.update_network(self.aqnetworks[ip], qipnetworks[ip]):
                # If the netmask did not change, then we're done with this
                # network
                del self.aqnetworks[ip]
                del qipnetworks[ip]
        self.commit_if_needed()

        # What is left after this point is additions, deletions, splits and
        # merges

        aqnets = self.aqnetworks.values()
        heapq.heapify(aqnets)
        qipnets = qipnetworks.values()
        heapq.heapify(qipnets)

        aqnet = heap_pop(aqnets)
        qipinfo = heap_pop(qipnets)
        while aqnet or qipinfo:
            # We have 3 cases regarding aqnet/qipinfo:
            # - One contains the other: this is a split or a merge
            # - aqnet.ip < qipinfo.address.ip (or there is no qipinfo): the
            #   network was deleted from QIP
            # - qipinfo.address.ip < aqnet.ip (or there is no aqnet): a new
            #   network was added to QIP
            if aqnet and qipinfo and (aqnet.ip in qipinfo.address or
                                      qipinfo.address.ip in aqnet.network):
                # This is a split or a merge. The trick here is to perform
                # multiple network additions/deletions inside the same
                # transaction even in incremental mode, to maintain relational
                # integrity

                startip = min(aqnet.ip, qipinfo.address.ip)
                prefixlen = min(aqnet.cidr, qipinfo.address.prefixlen)
                supernet = IPv4Network("%s/%s" % (startip, prefixlen))
                # We may modify aqnet.network below, so save the original value
                orig_net = aqnet.network

                # Always deleting & possibly recreating aqnet would make things
                # simpler, but we can't do that due to the unique constraint on
                # the IP address and the non-null foreign key constraints in
                # other tables. So we need a flag to remember if we want to keep
                # the original object or not
                if aqnet.ip == qipinfo.address.ip:
                    self.logger.client_info("Setting network {0:a} prefix "
                                            "length to {1}"
                                            .format(aqnet,
                                                    qipinfo.address.prefixlen))
                    aqnet.cidr = qipinfo.address.prefixlen
                    keep_aqnet = True
                else:
                    # This can happen if the network was split, and then the
                    # first subnet was deleted
                    keep_aqnet = False

                # Here we rely heavily on network sizes being a power of two, so
                # supernet is either equal to aqnet or to qipinfo - partial
                # overlap is not possible
                if orig_net == supernet:
                    # Split:
                    #  AQ:  ******** (one big network)
                    #  QIP: --**++++ (smaller networks, some may be missing)
                    if keep_aqnet:
                        # The first subnet was handled above by setting
                        # aqnet.cidr
                        qipinfo = heap_pop(qipnets)
                    else:
                        # The first subnet was deleted
                        pass
                    while qipinfo and qipinfo.address.ip in orig_net:
                        newnet = self.add_network(qipinfo)
                        # Redirect addresses from the split network to the new
                        # subnet
                        fix_foreign_links(self.session, aqnet, newnet)
                        qipinfo = heap_pop(qipnets)
                    if keep_aqnet:
                        self.check_split_network(aqnet)
                    else:
                        self.del_network(aqnet)
                    aqnet = heap_pop(aqnets)
                else:
                    # Merge:
                    #  AQ:  --++**** (smaller networks, some may be missing)
                    #  QIP: ******** (one big network)
                    if keep_aqnet:
                        # The first subnet was handled above by setting
                        # aqnet.cidr
                        newnet = aqnet
                        aqnet = heap_pop(aqnets)
                    else:
                        # The first subnet was missing from AQDB before
                        newnet = self.add_network(qipinfo)
                    while aqnet and aqnet.ip in newnet.network:
                        # Redirect addresses from the subnet to the merged
                        # network
                        fix_foreign_links(self.session, aqnet, newnet)
                        self.del_network(aqnet)
                        aqnet = heap_pop(aqnets)
                    qipinfo = heap_pop(qipnets)
            elif aqnet and (not qipinfo or aqnet.ip < qipinfo.address.ip):
                # Network is deleted
                self.del_network(aqnet)
                aqnet = heap_pop(aqnets)
            else:
                # New network
                self.add_network(qipinfo)
                qipinfo = heap_pop(qipnets)

            self.commit_if_needed()
        self.session.flush()

        if self.errors:
            if self.incremental:
                msg = ""
            else:
                msg = "No changes applied because of errors."
            raise PartialError(success=[], failed=self.errors, success_msg=msg)

