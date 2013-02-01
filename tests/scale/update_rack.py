#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
"""Update the dummy information for a rack of machines on a /26."""


import os
import sys

from common import AQRunner, TestNetwork, TestRack


def update_rack(building, rackid, newnetid, aqservice, aqhost, aqport):
    aq = AQRunner(aqservice=aqservice, aqhost=aqhost, aqport=aqport)
    rack = TestRack(building, rackid)
    rc = aq.wait(["ping"])
    for half in [0, 1]:
        newnetwork = TestNetwork(newnetid, half)
        tor_switch = rack.get_tor_switch(half)
        print "Updating tor_switch %s" % tor_switch
        rc = aq.wait(["update", "interface", "--machine", tor_switch,
            "--interface", "xge49",
            "--mac", newnetwork.get_mac(0), "--ip", newnetwork.get_ip(0)])
        for offset in range(1, 49):
            machine = rack.get_machine(half, offset)
            print "Updating machine %s" % machine
            rc = aq.wait(["update", "interface", "--machine", machine,
                "--interface", "eth0", "--mac", newnetwork.get_mac(offset),
                "--ip", newnetwork.get_ip(offset)])
            host = rack.get_host(half, offset)
            print "reconfiguring host %s" % host
            rc = aq.wait(["reconfigure", "--hostname", host])


if __name__=='__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-b", "--building", dest="building", type="string",
                      help="The building name to use")
    parser.add_option("-r", "--rack", dest="rack", type="int",
                      help="The rack id to update, 0-7")
    parser.add_option("-s", "--subnet", dest="subnet", type="int",
                      help="The new subnet to use, 0-7")
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

    update_rack(options.building, options.rack, options.subnet,
                options.aqservice, options.aqhost, options.aqport)
