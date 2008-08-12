#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header: //eai/aquilon/aqd/1.2.1/src/etc/default-template.py#1 $
# $Change: 645284 $
# $DateTime: 2008/07/09 19:56:59 $
# $Author: wesleyhe $
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Sets up an empty database with any info needed for the tests."""


from common import AQRunner


def setup():
    aq = AQRunner()
    # FIXME: What does this look like in prod?
    rc = aq.wait(["add", "cpu", "--cpu", "rs8000 asic",
        "--vendor", "ibm", "--speed", "500"])
    # FIXME: Vendor is bnt
    rc = aq.wait(["add", "model", "--name", "rs8000", "--vendor", "verari",
        "--type", "tor_switch", "--cputype", "rs8000 asic",
        "--cpunum", "1", "--mem", "256", "--disktype", "flash", 
        "--disksize", "1", "--nics", "4"])
    rc = aq.wait(["add", "domain", "--domain", "testdom"])
    # FIXME: The domain might need to have a building added...
    services = [["afs", "q.ny.ms.com"],
                ["bootserver", "np.test"],
                ["dns", "nyinfratest"],
                ["ntp", "pa.ny.na"],
                ["syslogng", "nyb6.np.1"]]
    for (service, instance) in services:
        rc = aq.wait(["add", "service", "--service", service])
        rc = aq.wait(["add", "required", "service", "--service", service,
            "--archetype", "aquilon"])
        rc = aq.wait(["add", "service", "--service", service,
            "--instance", instance])
        rc = aq.wait(["map", "service", "--service", service,
            "--instance", instance, "--building", "np"])

if __name__=='__main__':
    setup()
