# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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

import os
from csv import DictReader
import cPickle as pickle
from ipaddr import IPv4Network, IPv4Address

# Ranges for dynamic network allocation. The idea is to allocate a /N network
# inside 10.N.0.0/16.
SUBNET_RANGE = {
    24: IPv4Network('10.24.0.0/16'),
    25: IPv4Network('10.25.0.0/16'),
    26: IPv4Network('10.26.0.0/16'),
    27: IPv4Network('10.27.0.0/16')}


class DummyIP(IPv4Address):
    def __init__(self, *args, **kwargs):
        super(DummyIP, self).__init__(*args, **kwargs)

        octets = [int(i) for i in str(self).split('.')]
        self.mac = "02:02:%02x:%02x:%02x:%02x" % tuple(octets)


class NetworkInfo(IPv4Network):
    def __init__(self, name, cidr, nettype, loc_type, loc_name, side="a",
                 autocreate=False):
        super(NetworkInfo, self).__init__(cidr)

        self.name = name
        self.nettype = nettype
        self.usable = list()
        self.reserved = list()
        self.loc_type = loc_type
        self.loc_name = loc_name
        self.side = side

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
            offsets = [39]
        else:
            offsets = []

        for offset in offsets:
            self.reserved.append(DummyIP(self[offset]))

        first_usable = max(offsets or [4]) + 1
        for i in range(first_usable, self.numhosts - 1):
            self.usable.append(DummyIP(self[i]))

    @property
    def gateway(self):
        return self[1]

    def __getitem__(self, idx):
        # Cast the result to DummyIP, so the .mac property can be used
        return DummyIP(super(NetworkInfo, self).__getitem__(idx))


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
                                side=row["side"], autocreate=row["autocreate"])

                # Sanity checks
                if row["name"] in self.networks:
                    raise KeyError("Duplicate name '%s' in %s" % (row["name"],
                                                                  filename))
                for existing in self.networks.itervalues():
                    if n in existing or existing in n:
                        raise ValueError("Overlapping networks %s and %s in %s"
                                         % (existing, n, filename))

                for dynrange in SUBNET_RANGE.itervalues():
                    if n in dynrange or dynrange in n:
                        raise ValueError("Range %s is reserved for dynamic "
                                         "allocation" % dynrange)

                self.networks[row["name"]] = n

        # Load dynamic networks
        if os.path.exists(self.statedir):
            for name in os.listdir(self.statedir):
                with open(os.path.join(self.statedir, name), "r") as f:
                    net = pickle.load(f)
                    self.networks[net.name] = net
        else:
            os.makedirs(self.statedir)

    def __getitem__(self, name):
        return self.networks[name]

    def __iter__(self):
        for net in self.networks.itervalues():
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
        for net in range.iter_subnets(new_prefix=prefixlength):
            statefile = os.path.join(self.statedir, "%s" % net.ip)
            if os.path.exists(statefile):
                continue

            result = NetworkInfo(name, str(net), network_type, loc_type,
                                 loc_name, side)
            break

        if not result:
            raise ValueError("Could not allocate network of size /%d" %
                             prefixlength)

        command = ["add_network", "--network", name, "--ip", result.ip,
                   "--netmask", result.netmask,
                   "--" + loc_type, loc_name, "--type", network_type]
        if comments:
            command.extend(["--comments", comments])
        testsuite.noouttest(command)

        with open(statefile, "w") as f:
            pickle.dump(result, f)

        self.networks[name] = result

        return result

    def dispose_network(self, testsuite, name):
        if name not in self.networks:
            raise ValueError("Trying to dispose unknown network %s" % name)

        net = self.networks[name]

        command = ["del_network", "--ip", net.ip]
        testsuite.noouttest(command)

        statefile = os.path.join(self.statedir, "%s" % net.ip)
        os.unlink(statefile)
        del self.networks[name]
