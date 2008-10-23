#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Sets up an empty database with any info needed for the tests."""


import os
import sys

if __name__=='__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..',
                                                     "lib", "python2.5")))

from common import AQBroker, AQRunner


def setup():
    broker = AQBroker()
    broker.stop()
    broker.initialize()
    rc = broker.start()
    if rc:
        print >>sys.stderr, "Broker start had return code %d" % rc
    aq = AQRunner(aqservice=broker.get_aqservice())
    rc = aq.wait(["add", "domain", "--domain", "testdom"])
    rc = aq.wait(["add", "aurora", "host", "--hostname", "nyaqd1"])
    services = [["afs", "q.ny.ms.com"],
                ["ntp", "pa.ny.na"],
                ["bootserver", "np.test"],
                ["dns", "nyinfratest"],
                ["syslogng", "nyb6.np.1"],
                ["lemon", "lemon.ny"],
                ["aqd", "ny-prod"],
                ["perfdata", "ny.a"]]
    for (service, instance) in services:
        rc = aq.wait(["add", "service", "--service", service])
        rc = aq.wait(["add", "required", "service", "--service", service,
            "--archetype", "aquilon"])
        rc = aq.wait(["add", "service", "--service", service,
            "--instance", instance])
        rc = aq.wait(["map", "service", "--service", service,
            "--instance", instance, "--building", "np"])
        rc = aq.wait(["bind", "server", "--service", service,
            "--instance", instance, "--hostname", "nyaqd1.ms.com"])

if __name__=='__main__':
    setup()
