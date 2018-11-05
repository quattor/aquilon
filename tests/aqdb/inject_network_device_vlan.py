#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""Fake the bind port group command with network device not virtuals"""
import sys
import site
import os
import logging

# -- begin path_setup --
TESTDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
SRCDIR = os.path.dirname(TESTDIR)
LIBDIR = os.path.join(SRCDIR, 'lib')

site.addsitedir(LIBDIR)
# -- end path_setup --

import ms.version
ms.version.addpkg('mako', '1.0.4')
ms.version.addpkg('twisted', '15.4.0')
ms.version.addpkg('zope.interface', '4.5.0')
ms.version.addpkg('six', '1.9.0')

from six import text_type
import zope.interface
import mako
import twisted
import argparse

from aquilon.aqdb.model import PortGroup, Base, NetworkDevice, VlanInfo
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.aqdb.db_factory import DbFactory
from aquilon.worker.templates.base import PlenaryCollection
from ipaddress import IPv4Address
from aquilon.worker.dbwrappers.change_management import ChangeManagement

def inject_data(network_device, to_bind):
    # Get session
    db = DbFactory()
    session = db.Session()
    # Get plenaries:
    plenaries = PlenaryCollection()
    dbnetdev = NetworkDevice.get_unique(session, network_device,
                                        compel=True)
    for e in to_bind:
        tag = e[0]
        networkip = e[1]
        networkip = IPv4Address(text_type(networkip))
        dbvi = VlanInfo.get_unique(session, vlan_id=tag, compel=False)
        type = dbvi.vlan_type
        dbnetwork = get_net_id_from_ip(session, networkip,
                                       network_environment='internal')
        if dbnetwork.port_group:
            pg = dbnetwork.port_group
        else:
            dbnetwork.port_group = PortGroup(network_tag=tag, usage=type)
        dbnetwork.lock_row()
        dbnetdev.port_groups.append(dbnetwork.port_group)
        session.flush()
        plenaries.add(dbnetdev)
        plenaries.write()
        session.commit()
    session.close()


parser = argparse.ArgumentParser()
parser.add_argument('-v', '--vlan', action='append', nargs=2, required=True,
                    help='use --vlan TAG IP to bind a port group')
parser.add_argument('-n', '--network_device', required=True)
args = parser.parse_args()
inject_data(args.network_device, args.vlan)

