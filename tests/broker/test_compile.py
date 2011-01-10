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
"""Module for testing the compile command."""

import os
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestCompile(TestBrokerCommand):

    def test_000_precompile(self):
        # Before the tests below, make sure everything is up to date.
        command = "compile --domain unittest"
        (out, err) = self.successtest(command.split(" "))

    def test_100_addchange(self):
        # Touch the template used by utsi1 clients to trigger a recompile.
        domaindir = os.path.join(self.config.get("broker", "domainsdir"),
                                 "unittest")
        template = os.path.join(domaindir, "service", "utsvc", "utsi1",
                                "client", "config.tpl")
        f = open(template)
        try:
            contents = f.readlines()
        finally:
            f.close()
        contents.append("#Added by unittest broker/test_compile\n")
        f = open(template, 'w')
        try:
            f.writelines(contents)
        finally:
            f.close()

    def test_200_compileunittest(self):
        command = "compile --domain unittest"
        (out, err) = self.successtest(command.split(" "))
        # The idea is to check that only that hosts that needed to
        # be compiled actually were. Note that clusters and other
        # included profiles might get recompiled, so we need to adjust
        # the number we're looking for based on everything. It might
        # be better to look for the objects being processed and checking
        # that the numbers a/b (for processing) are different.
        self.matchoutput(err, "16/16 compiled", command)

    def test_300_compilehost(self):
        command = "compile --hostname unittest02.one-nyp.ms.com"
        (out, err) = self.successtest(command.split(" "))
        # This should have been compiled above...
        self.matchoutput(err, "0/1 object template(s) being processed",
                         command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCompile)
    unittest.TextTestRunner(verbosity=2).run(suite)
