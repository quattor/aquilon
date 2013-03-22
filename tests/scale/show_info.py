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
