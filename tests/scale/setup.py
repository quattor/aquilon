#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013  Contributor
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
"""Sets up an empty database with any info needed for the tests."""

from __future__ import print_function

import os
import sys

if __name__=='__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', "lib")))

from common import AQRunner
from broker import AQBroker


def setup():
    broker = AQBroker()
    broker.stop()
    broker.initialize()
    rc = broker.start()
    if rc:
        print("Broker start had return code %d" % rc, file=sys.stderr)
    aq = AQRunner(aqservice=broker.get_aqservice())
    rc = aq.wait(["add", "domain", "--domain", "testdom_odd"])
    rc = aq.wait(["add", "domain", "--domain", "testdom_even"])
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
