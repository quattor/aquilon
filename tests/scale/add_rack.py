#!/usr/bin/env python2.6
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
"""Add dummy information for a rack of machines on a /26."""


import os
import sys

from common import AQRunner, TestNetwork, TestRack


def add_rack(building, rackid, netid, aqservice, aqhost, aqport):
    aq = AQRunner(aqservice=aqservice, aqhost=aqhost, aqport=aqport)
    rack = TestRack(building, rackid)
    rc = aq.wait(["ping"])
    for half in [0, 1]:
        network = TestNetwork(netid, half)
        tor_switch = rack.get_tor_switch(half)
        "Adding a tor_switch"
        rc = aq.wait(["add", "tor_switch", "--tor_switch", tor_switch,
            "--building", building, "--rackid", rack.rackid,
            "--model", "rs g8000", "--interface", "xge49",
            "--rackrow", rack.row, "--rackcolumn", rack.column,
            "--mac", network.get_mac(0), "--ip", network.get_ip(0)])
        domain = "testdom_odd" if rackid % 2 else "testdom_even"
        for offset in range(1, 49):
            machine = rack.get_machine(half, offset)
            print "Adding machine %s" % machine
            rc = aq.wait(["add", "machine", "--machine", machine,
                "--model", "vb1205xm", "--rack", rack.get_rack()])
            print "Adding an interface with %s" % network.get_mac(offset)
            rc = aq.wait(["add", "interface", "--machine", machine,
                          "--interface", "eth0",
                          "--mac", network.get_mac(offset)])
            host = rack.get_host(half, offset)
            print "Adding host %s with %s" % (host, network.get_ip(offset))
            rc = aq.wait(["add", "host", "--machine", machine,
                          "--hostname", host, "--archetype", "aquilon",
                          "--domain", domain, "--buildstatus", "blind",
                          "--ip", network.get_ip(offset)])
            print "make aquilon for host %s" % host
            rc = aq.wait(["make", "aquilon", "--hostname", host,
                          "--os", "linux/4.0.1-x86_64",
                          "--personality", "compileserver"])


if __name__=='__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-b", "--building", dest="building", type="string",
                      help="The building name to use")
    parser.add_option("-r", "--rack", dest="rack", type="int",
                      help="The rack id to use, 0-7")
    parser.add_option("-s", "--subnet", dest="subnet", type="int",
                      help="The subnet to use, 0-7")
    parser.add_option("-a", "--aqservice", dest="aqservice", type="string",
                      help="The service name to use when connecting to aqd")
    parser.add_option("-t", "--aqhost", dest="aqhost", type="string",
                      help="The aqd host to connect to")
    parser.add_option("-p", "--aqport", dest="aqport", type="string",
                      help="The port to use when connecting to aqd")
    (options, args) = parser.parse_args()
    if not options.building:
        parser.error("Missing option --building")
    if options.rack is None:
        parser.error("Missing option --rack")
    if options.rack not in range(8):
        parser.error("--rack must be 0-7")
    if options.subnet is None:
        parser.error("Missing option --subnet")
    if options.subnet not in range(8):
        parser.error("--subnet must be 0-7")

    add_rack(options.building, options.rack, options.subnet,
             options.aqservice, options.aqhost, options.aqport)
