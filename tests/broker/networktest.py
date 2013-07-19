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

from ipaddr import IPv4Network, IPv4Address


class DummyIP(IPv4Address):
    def __init__(self, *args, **kwargs):
        super(DummyIP, self).__init__(*args, **kwargs)

        octets = [int(i) for i in str(self).split('.')]
        self.mac = "02:02:%02x:%02x:%02x:%02x" % tuple(octets)


class NetworkInfo(IPv4Network):
    def __init__(self, cidr, nettype, autocreate):
        super(NetworkInfo, self).__init__(cidr)

        self.nettype = nettype
        self.usable = list()
        self.reserved = list()

        if autocreate == "True":
            self.autocreate = True
        elif autocreate == "False":
            self.autocreate = False
        else:
            raise ValueError("Invalid value for autocreate: %s" % autocreate)

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

        self.unknown = list()
        self.tor_net = list()
        self.tor_net2 = list()
        self.vm_storage_net = list()
        self.vpls = list()
        self.all = list()

        self.networks = {}

        typemap = {"unknown": self.unknown,
                   "tor_net": self.tor_net,
                   "tor_net2": self.tor_net2,
                   "vm_storage_net": self.vm_storage_net,
                   "vpls": self.vpls}

        dir = config.get("unittest", "datadir")
        filename = os.path.join(dir, "networks.csv")
        with open(filename, "r") as datafile:
            # Filter out comments
            lines = [line for line in datafile if not line.startswith('#')]
            reader = DictReader(lines)
            for row in reader:
                n = NetworkInfo(row["cidr"], row["type"], row["autocreate"])
                if row["type"] in typemap:
                    typemap[row["type"]].append(n)
                if row["autocreate"] == "True":
                    self.all.append(n)

                # Sanity checks
                if row["name"] in self.networks:
                    raise KeyError("Duplicate name '%s' in %s" % (row["name"],
                                                                  filename))
                for existing in self.networks.itervalues():
                    if n in existing or existing in n:
                        raise ValueError("Overlapping networks %s and %s in %s"
                                         % (existing, n, filename))

                self.networks[row["name"]] = n

    def __getitem__(self, name):
        return self.networks[name]

    def __iter__(self):
        for net in self.networks.itervalues():
            yield net
