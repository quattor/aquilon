#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
""" tests network """
from utils import add, commit, load_classpath
load_classpath()

import aquilon.aqdb.depends

from aquilon.aqdb.model import Network, Gateway, Location, Building
from aquilon.aqdb.db_factory import DbFactory

from nose.tools import raises

db = DbFactory()
sess = db.Session()
net = sess.query(Network).first()

TEST_IP = '8.9.9.1'
TEST_BCAST = '8.9.9.128'
TEST_NAME = 'test_vpls_net'

def setup():
    print 'set up'
    clean_up()

def teardown():
    print 'tear down'
    #clean_up()

def clean_up():
    del_vpls_net()
    #explicitly not deleting gateways to test cascaded deletion in line

def del_vpls_net():
    mynet = sess.query(Network).filter_by(name=TEST_NAME).all()
    if mynet:
        sess.query(Network).filter_by(name=TEST_NAME).delete()
        print 'about to commit'
        commit(sess)
        print 'deleted %s test networks'%(len(mynet))

def test_location():
    assert net.location

def test_addresses():
    assert net.addresses()

def test_netmask():
    assert net.netmask()

def test_first_host():
    assert net.first_host()

def test_no_gateway():
    assert len(net.gateways) is 0

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

def test_network_gateway_cascade_delete():
    """ the test network is deleted at the begining and should cascade to the
        gateways we created, leaving the table empty here. We can't query by
        network (would presumably more accurate) it's already been wiped out """

    gws = sess.query(Gateway).all()
    if gws:
        print 'found gateways %s'%(gws)
    assert len(gws) is 0

def test_create_vpls_network():
    loc1 = Building.get_by('name', 'dd', sess)[0]

    vpls_net1 = Network(name=TEST_NAME, location=loc1, ip=TEST_IP, cidr=25,
                        network_type='stretch', mask=128, bcast=TEST_BCAST)
    add(sess, vpls_net1)
    commit(sess)

    assert isinstance(vpls_net1, aquilon.aqdb.model.network.Network)
    print vpls_net1

def test_add_gateways():
    vnet = sess.query(Network).filter_by(name=TEST_NAME).first()
    assert vnet

    loc1 = Building.get_by('name', 'dd', sess)[0]
    assert loc1

    loc2 = Building.get_by('name', 'ds', sess)[0]
    assert loc2

    gw1 = Gateway(network=vnet, location=loc1, ip='8.9.9.2')
    gw2 = Gateway(network=vnet, location=loc2, ip='8.9.9.3')

    add(sess, gw1)
    add(sess, gw2)

    commit(sess)
    assert gw1
    assert gw2

    print gw1
    print gw2
    print vnet
    print 'network has gateways %s'% (vnet.gateways)

def test_plural_network_location():
    vnet = sess.query(Network).filter_by(name=TEST_NAME).first()

    assert len(vnet.locations) is 2
    print 'network locations %s'% (vnet.locations)


@raises(ValueError)
def test_stretch_validator():
    #TODO: construct a network instead of using the global 'net'
    assert net.network_type != 'stretch'

    loc = Building.get_by('name', 'dd', sess)[0]
    assert loc

    gw = Gateway(network=net, location=loc, ip='8.9.9.4')
    add(sess, gw)
    commit(sess)

if __name__ == "__main__":
    import nose
    nose.runmodule()
