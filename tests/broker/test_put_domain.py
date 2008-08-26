#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the put domain command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestPutDomain(TestBrokerCommand):

    def testmakechange(self):
        template = os.path.join(self.scratchdir, "changetest1", "aquilon",
                "archetype", "base.tpl")
        f = open(template)
        try:
            contents = f.readlines()
        finally:
            f.close()
        contents.append("#Added by unittest\n")
        f = open(template, 'w')
        try:
            f.writelines(contents)
        finally:
            f.close()
        self.gitcommand(["commit", "-a", "-m", "added unittest comment"],
                cwd=os.path.join(self.scratchdir, "changetest1"))

    def testputchangetest1domain(self):
        self.ignoreoutputtest(["put", "--domain", "changetest1"],
                env=self.gitenv(),
                cwd=os.path.join(self.scratchdir, "changetest1"))
        self.assert_(os.path.exists(os.path.join(
            self.scratchdir, "changetest1")))

    def testaddsiteut(self):
        sitedir = os.path.join(self.scratchdir, "unittest", "aquilon",
                "site", "americas", "ny", "ut")
        if not os.path.exists(sitedir):
            os.makedirs(sitedir)
        template = os.path.join(sitedir, "config.tpl")
        f = open(template, 'w')
        try:
            f.writelines("template site/americas/ny/ut/config;\n\n")
        finally:
            f.close()
        self.gitcommand(["add", "config.tpl"], cwd=sitedir)
        self.gitcommand(["commit", "-a", "-m", "added building ut"],
                cwd=os.path.join(self.scratchdir, "unittest"))

    def testaddutsi1(self):
        """utsi1 = unit test service instance 1"""
        sitedir = os.path.join(self.scratchdir, "unittest", "service",
                "utsvc", "utsi1", "client")
        if not os.path.exists(sitedir):
            os.makedirs(sitedir)
        template = os.path.join(sitedir, "config.tpl")
        f = open(template, 'w')
        try:
            f.writelines("template service/utsvc/utsi1/client/config;\n\n")
        finally:
            f.close()
        self.gitcommand(["add", "config.tpl"], cwd=sitedir)
        self.gitcommand(["commit", "-a", "-m",
                "added unit test service instance 1"],
                cwd=os.path.join(self.scratchdir, "unittest"))

    def testaddutsi2(self):
        """utsi1 = unit test service instance 2"""
        sitedir = os.path.join(self.scratchdir, "unittest", "service",
                "utsvc", "utsi2", "client")
        if not os.path.exists(sitedir):
            os.makedirs(sitedir)
        template = os.path.join(sitedir, "config.tpl")
        f = open(template, 'w')
        try:
            f.writelines("template service/utsvc/utsi2/client/config;\n\n")
        finally:
            f.close()
        self.gitcommand(["add", "config.tpl"], cwd=sitedir)
        self.gitcommand(["commit", "-a", "-m",
                "added unit test service instance 2"],
                cwd=os.path.join(self.scratchdir, "unittest"))

    def testputunittestdomain(self):
        self.ignoreoutputtest(["put", "--domain", "unittest"],
                env=self.gitenv(),
                cwd=os.path.join(self.scratchdir, "unittest"))
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "templatesdir"), "unittest", "aquilon",
            "site", "americas", "ny", "ut", "config.tpl")))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPutDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)

