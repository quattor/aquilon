#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2016,2017,2018  Contributor
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

import json
import os
import re
import socket
import sys

LIBDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
SBINDIR = os.path.join(LIBDIR, "..", "sbin")

if LIBDIR not in sys.path:
    sys.path.append(LIBDIR)

# sbin/aqd.py, we'll start it after the patch is done
if SBINDIR not in sys.path:
    sys.path.append(SBINDIR)

from aquilon.aqdb import depends  # pylint: disable=W0611
from aquilon.worker import depends  # pylint: disable=W0611
from aquilon.config import Config

# dwim options parser
for i in range(0, len(sys.argv)):
    if sys.argv[i] == "--config":
        configpath = sys.argv[i + 1]
        break

config = Config(configfile=configpath)


# do the patches


def fake_gethostbyname(hostname):
    try:
        host_ip = None
        # for templates/index.py
        if hostname == config.get("broker", "bind_address"):
            host_ip = gethostbyname_orig(hostname)
        else:
            # faking hostip
            fake_hosts_file = config.get('unittest', 'fake_hosts_location')
            fake_hosts = {}
            with open(fake_hosts_file, 'r') as f:
                fake_hosts = json.load(f)

            dsdb_host = fake_hosts.get(hostname, [])
            # strip domain part
            if not dsdb_host and hostname.find(".") > -1:
                dsdb_host = fake_hosts.get(hostname[:hostname.find(".")])

            if len(dsdb_host) == 1:
                dsdb_host = dsdb_host[0]
            else:
                raise socket.gaierror(-2, "Name or service not known")

            primary_name = dsdb_host["primary_hostname"]
            for interf in dsdb_host["interfaces"]:
                if interf["interface_hostname"] == primary_name and interf["IP_address"]:
                    host_ip = interf["IP_address"]
                    break

        if not host_ip:
            raise socket.gaierror(-2, "Name or service not known")

        return host_ip

    except IOError as e:
        # To have the cause in aqd.log
        raise socket.gaierror(-2, "Name or service not known %s" % e)

gethostbyname_orig = socket.gethostbyname
socket.gethostbyname = fake_gethostbyname

# worker/resources.py depends on it.
sys.argv[0] = os.path.join(SBINDIR, "aqd.py")

# start the broker
import aqd
aqd.run()
