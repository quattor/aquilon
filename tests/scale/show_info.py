#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Run different show commands."""


import os
import sys

from common import AQRunner


def show_info(aqservice):
    aq = AQRunner(aqservice=aqservice)
    rc = aq.wait(["ping"])
    rc = aq.wait(["show", "host", "--all"])
    rc = aq.wait(["show", "domain", "--all"])
    rc = aq.wait(["show", "hostiplist"])
    rc = aq.wait(["show", "hostmachinelist"])
    rc = aq.wait(["show", "cpu", "--all"])
    rc = aq.wait(["show", "model", "--type", "blade"])
    rc = aq.wait(["show", "service", "--all"])
    rc = aq.wait(["show", "archetype"])
    rc = aq.wait(["show", "map", "--building", "np"])
    rc = aq.wait(["show", "chassis"])
    rc = aq.wait(["show", "rack", "--all"])
    rc = aq.wait(["show", "building"])
    rc = aq.wait(["show", "city"])
    rc = aq.wait(["show", "country"])
    rc = aq.wait(["show", "continent"])
    rc = aq.wait(["show", "hub"])
    rc = aq.wait(["show", "machine", "--all"])
    rc = aq.wait(["show", "tor_switch", "--model", "rs8000"])
    rc = aq.wait(["show", "principal"])


if __name__=='__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-a", "--aqservice", dest="aqservice", type="string",
                      help="The service name to use when connecting to aqd")
    (options, args) = parser.parse_args()

    show_info(options.aqservice)

