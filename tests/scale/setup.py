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
"""Sets up an empty database with any info needed for the tests."""


import os
import sys

if __name__=='__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..',
                                                     "lib", "python2.6")))

from common import AQRunner
from broker import AQBroker


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
