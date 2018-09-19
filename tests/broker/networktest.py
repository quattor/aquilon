# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013,2014,2015,2017  Contributor
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
""" Helper classes for network testing """

from functools import total_ordering
import os
from csv import DictReader

import six.moves.cPickle as pickle  # pylint: disable=F0401
from six import itervalues, text_type

from ipaddress import (IPv4Network, IPv4Address, IPv6Network, IPv6Address,
                       ip_network, ip_address)

# Ranges for dynamic network allocation. The idea is to allocate a /N network
# inside 10.N.0.0/16.
SUBNET_RANGE = {
    24: IPv4Network(u'10.24.0.0/16'),
    25: IPv4Network(u'10.25.0.0/16'),
    26: IPv4Network(u'10.26.0.0/16'),
    27: IPv4Network(u'10.27.0.0/16'),
    28: IPv4Network(u'10.28.0.0/16')}


@total_ordering
class DummyIP(object):
    """
    Wrapper around an IP address

    This class should work like IPv[46]Address, but it allows attaching some
    convenience methods like MAC address generation.
    """

    def __init__(self, *args, **kwargs):
        self._ip = ip_address(*args, **kwargs)

        if isinstance(self._ip, IPv4Address):
            octets = [int(i) for i in str(self._ip).split('.')]
            self.mac = "02:02:%02x:%02x:%02x:%02x" % tuple(octets)
        else:
            # FIXME
            self.mac = None

    def __str__(self):
        return str(self._ip)

    def __repr__(self):
        return repr(self._ip)

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._ip == other._ip
        else:
            return self._ip == other

    def __lt__(self, other):
        if isinstance(other, type(self)):
            return self._ip < other._ip
        else:
            return self._ip < other

    def __int__(self):
        return int(self._ip)

    def __hash__(self):
        return hash(self._ip)

    def __add__(self, other):
        return DummyIP(self._ip + other)

    def __sub__(self, other):
        return DummyIP(self._ip - other)

    def __getattr__(self, name):
        # Proxy lookups to the wrapped network object
        if "_ip" not in self.__dict__:
            # Happens while unpickling
            raise AttributeError
        return getattr(self._ip, name)


class IPGenerator(object):
    """
    Helper for indexing into the usable IP range of a network
    """

    def __init__(self, network, offset):
        self.network = network
        self.offset = offset

    def __getitem__(self, index):
        if index < 0:
            # Skip the broadcast address
            ip = DummyIP(self.network[index - 1])
            if ip < self.network[self.offset]:
                raise IndexError("Index too small")
        else:
            ip = DummyIP(self.network[index + self.offset])
            if ip >= self.network.broadcast_address:
                raise IndexError("Index too big")
        return ip


@total_ordering
class NetworkInfo(object):
    """
    Wrapper around a network

    This class should work like IPv[46]Network, but it allows attaching
    Aquilon-related metadata, and a few convenience methods.
    """

    def __init__(self, name, cidr, nettype, loc_type, loc_name, side="a",
                 autocreate=False, comments=None):
        if isinstance(cidr, (IPv4Network, IPv6Network)):
            self._network = cidr
        else:
            self._network = ip_network(text_type(cidr))

        self.name = name
        self.nettype = nettype
        self.reserved = list()
        self.loc_type = loc_type
        self.loc_name = loc_name
        self.side = side
        self.comments = comments

        if isinstance(autocreate, bool):
            self.autocreate = autocreate
        elif autocreate == "True":
            self.autocreate = True
        elif autocreate == "False":
            self.autocreate = False
        else:
            raise ValueError("Invalid value for autocreate: %r" % autocreate)

        if nettype == 'tor_net':
            offsets = [6, 7]
        elif nettype == 'tor_net2':
            offsets = [7, 8]
        elif nettype == 'vm_storage_net':
            offsets = [8]
        else:
            offsets = []

        for offset in offsets:
            self.reserved.append(DummyIP(self[offset]))

        first_usable = max(offsets or [4]) + 1
        self.usable = IPGenerator(self, first_usable)

    def __getattr__(self, name):
        # Proxy lookups to the wrapped network object
        if "_network" not in self.__dict__:
            # Happens while unpickling
            raise AttributeError
        return getattr(self._network, name)

    def __getitem__(self, idx):
        # Cast the result to DummyIP, so the .mac property can be used
        return DummyIP(self._network[idx])

    def __str__(self):
        return str(self._network)

    def __repr__(self):
        return repr(self._network)

    def __contains__(self, other):
        # Using a network on the left hand side of "in" works with ipaddr, but
        # will return the wrong answer with ipaddress.
        assert isinstance(other, (IPv4Address, IPv6Address, DummyIP))
        return other in self._network

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._network == other._network
        else:
            return self._network == other

    def __lt__(self, other):
        if isinstance(other, type(self)):
            return self._network < other._network
        else:
            return self._network < other

    def __hash__(self):
        return hash(self._network)

    @property
    def gateway(self):
        return self[1]

    @property
    def ip(self):
        return DummyIP(self._network.network_address)

    def subnet(self, new_prefix=None):
        return [NetworkInfo(str(net.network_address), net, self.nettype,
                            self.loc_type, self.loc_name, self.side)
                for net in self._network.subnets(new_prefix=new_prefix)]

    def subnets(self, new_prefix=None):
        for net in self._network.subnets(new_prefix=new_prefix):
            yield NetworkInfo(str(net.network_address), net, self.nettype,
                              self.loc_type, self.loc_name, self.side)

    @property
    def is_ipv4(self):
        return isinstance(self._network, IPv4Network)

    @property
    def is_ipv6(self):
        return isinstance(self._network, IPv6Network)


class DummyNetworks(object):
    # Borg
    __shared_state = {}

    def __init__(self, config, *args, **kwargs):
        self.__dict__ = self.__shared_state
        if getattr(self, "unknown", None):
            return
        object.__init__(self, *args, **kwargs)

        self.statedir = os.path.join(config.get("unittest", "scratchdir"),
                                     "networks")
        self.networks = {}

        dir = config.get("unittest", "datadir")
        filename = os.path.join(dir, "networks.csv")
        with open(filename, "r") as datafile:
            # Filter out comments
            lines = [line for line in datafile if not line.startswith('#')]
            reader = DictReader(lines)
            for row in reader:
                n = NetworkInfo(row["name"], row["cidr"], row["type"],
                                row["loc_type"], row["loc_name"],
                                side=row["side"], autocreate=row["autocreate"],
                                comments=row["comments"])

                # Sanity checks
                if row["name"] in self.networks:
                    raise KeyError("Duplicate name '%s' in %s" % (row["name"],
                                                                  filename))
                for existing in itervalues(self.networks):
                    if n.overlaps(existing):
                        raise ValueError("Overlapping networks %s and %s in %s"
                                         % (existing, n, filename))

                for dynrange in itervalues(SUBNET_RANGE):
                    if n.overlaps(dynrange):
                        raise ValueError("Range %s is reserved for dynamic "
                                         "allocation" % dynrange)

                self.networks[row["name"]] = n

        # Load dynamic networks
        if os.path.exists(self.statedir):
            for name in os.listdir(self.statedir):
                with open(os.path.join(self.statedir, name), "rb") as f:
                    net = pickle.load(f)
                    self.networks[net.name] = net
        else:
            os.makedirs(self.statedir)

    def __getitem__(self, name):
        return self.networks[name]

    def __iter__(self):
        for net in itervalues(self.networks):
            yield net

    def allocate_network(self, testsuite, name, prefixlength, network_type,
                         loc_type, loc_name, side='a', comments=None):
        if prefixlength not in SUBNET_RANGE:
            raise ValueError("There's no address range defined for /%d networks"
                             % prefixlength)
        if name in self.networks:
            raise ValueError("There's already a network named %s" % name)

        range = SUBNET_RANGE[prefixlength]
        result = None
        for net in range.subnets(new_prefix=prefixlength):
            statefile = os.path.join(self.statedir, "%s" % net.network_address)
            if os.path.exists(statefile):
                continue

            result = NetworkInfo(name, str(net), network_type, loc_type,
                                 loc_name, side)
            break

        if not result:
            raise ValueError("Could not allocate network of size /%d" %
                             prefixlength)

        command = ["add_network", "--network", name,
                   "--ip", result.network_address,
                   "--netmask", result.netmask,
                   "--" + loc_type, loc_name, "--type", network_type]
        if comments:
            command.extend(["--comments", comments])
        testsuite.noouttest(command)

        with open(statefile, "wb") as f:
            pickle.dump(result, f, -1)

        self.networks[name] = result

        return result

    def dispose_network(self, testsuite, name):
        if name not in self.networks:
            raise ValueError("Trying to dispose unknown network %s" % name)

        net = self.networks[name]

        command = ["del_network", "--ip", net.network_address]
        testsuite.noouttest(command)

        statefile = os.path.join(self.statedir, "%s" % net.network_address)
        os.unlink(statefile)
        del self.networks[name]
