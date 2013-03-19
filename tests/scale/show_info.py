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
"""Run different show commands."""


import os
import sys

from common import AQRunner


def show_info(aqservice, aqhost, aqport):
    aq = AQRunner(aqservice=aqservice, aqhost=aqhost, aqport=aqport)
    rc = aq.wait(["ping"])
    rc = aq.wait(["show", "host", "--all"])
    rc = aq.wait(["show", "domain", "--all"])
    rc = aq.wait(["show", "hostiplist"])
    rc = aq.wait(["show", "hostmachinelist"])
    rc = aq.wait(["show", "cpu", "--all"])
    rc = aq.wait(["show", "model", "--type", "blade"])
    rc = aq.wait(["show", "service", "--all"])
    rc = aq.wait(["show", "archetype", "--all"])
    rc = aq.wait(["show", "map", "--building", "np"])
    rc = aq.wait(["show", "chassis", "--all"])
    rc = aq.wait(["show", "rack", "--all"])
    rc = aq.wait(["show", "building", "--all"])
    rc = aq.wait(["show", "city", "--all"])
    rc = aq.wait(["show", "country", "--all"])
    rc = aq.wait(["show", "continent", "--all"])
    rc = aq.wait(["show", "hub", "--all"])
    rc = aq.wait(["show", "machine", "--all"])
    rc = aq.wait(["show", "tor_switch", "--model", "rs g8000"])
    rc = aq.wait(["show", "principal", "--all"])


if __name__=='__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-a", "--aqservice", dest="aqservice", type="string",
                      help="The service name to use when connecting to aqd")
    parser.add_option("-t", "--aqhost", dest="aqhost", type="string",
                      help="The aqd host to connect to")
    parser.add_option("-p", "--aqport", dest="aqport", type="string",
                      help="The port to use when connecting to aqd")
    (options, args) = parser.parse_args()

    show_info(options.aqservice, options.aqhost, options.aqport)
