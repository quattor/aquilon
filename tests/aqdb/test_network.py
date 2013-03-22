#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
""" tests network """
from utils import load_classpath
load_classpath()

from aquilon.aqdb.model import Network
from aquilon.aqdb.db_factory import DbFactory

db = DbFactory()
sess = db.Session()
net = sess.query(Network).filter(Network.cidr != 32).first()


def setup():
    assert net, 'no network in test_network'

def test_location():
    assert net.location

def test_netmask():
    assert net.netmask()

def test_first_host():
    assert net.first_host()

def test_broadcast():
    assert net.last_host()

def test_cidr():
    assert net.cidr

def test_ip():
    assert net.ip

def test_name():
    assert net.name

def test_side():
    assert net.side

def test_type():
    assert net.network_type

if __name__ == "__main__":
    import nose
    nose.runmodule()
