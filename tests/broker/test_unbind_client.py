#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the unbind client command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestUnbindClient(TestBrokerCommand):

    def test_100_bind_unmapped(self):
        command = ["bind_client", "--hostname=unittest02.one-nyp.ms.com",
                   "--service=unmapped", "--instance=instance1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service unmapped instance instance1",
                         command)
        self.matchclean(out, "removing binding", command)

    def test_100_bind_unmapped_unbuilt(self):
        command = ["bind_client", "--hostname=aquilon94.aqd-unittest.ms.com",
                   "--service=unmapped", "--instance=instance1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "aquilon94.aqd-unittest.ms.com adding binding for "
                         "service unmapped instance instance1",
                         command)
        self.matchclean(out, "removing binding", command)

    def test_200_verify_bind_cat(self):
        command = ["cat", "--hostname=unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "unmapped", command)

    def test_200_verify_bind_cat_unbuilt(self):
        command = ["cat", "--hostname=aquilon94.aqd-unittest.ms.com"]
        out = self.internalerrortest(command)
        self.matchoutput(out, "No such file or directory", command)

    def test_300_unbind_unmapped(self):
        command = ["unbind_client", "--hostname=unittest02.one-nyp.ms.com",
                   "--service=unmapped"]
        self.noouttest(command)

    def test_300_unbind_unmapped_unbuilt(self):
        command = ["unbind_client", "--hostname=aquilon94.aqd-unittest.ms.com",
                   "--service=unmapped"]
        self.noouttest(command)

    def test_400_verify_unbind_search(self):
        command = ["search_host", "--hostname=unittest02.one-nyp.ms.com",
                   "--service=unmapped"]
        self.noouttest(command)

    def test_400_verify_unbind_search_unbuilt(self):
        command = ["search_host", "--hostname=aquilon94.aqd-unittest.ms.com",
                   "--service=unmapped"]
        self.noouttest(command)

    def test_400_verify_unbind_cat(self):
        command = ["cat", "--hostname=unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "unmapped", command)

    def test_400_verify_unbind_cat_unbuilt(self):
        command = ["cat", "--hostname=aquilon94.aqd-unittest.ms.com"]
        out = self.internalerrortest(command)
        self.matchoutput(out, "No such file or directory", command)

    def testrejectunbindrequired(self):
        command = "unbind client --hostname unittest02.one-nyp.ms.com --service afs"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "cannot unbind a required service", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnbindClient)
    unittest.TextTestRunner(verbosity=2).run(suite)
