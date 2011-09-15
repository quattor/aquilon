#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011  Contributor
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
"""Module for tests that bypass the aq client."""

import os
import sys
import unittest
import urllib

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))


from brokertest import TestBrokerCommand

# This is a bit rough now. There are some error conditions (like syntax checks
# for integer options) that are done by both the broker and the client. Testing
# that the broker really does the checks requires us bypassing the client.
class TestClientBypass(TestBrokerCommand):

    def urltest(self, path, expect_status, post=False, **kwargs):
        openport = self.config.get("broker", "openport")
        server = self.config.get("broker", "servername")
        url = "http://" + server + ":" + openport + path
        if post:
            data = urllib.urlencode(kwargs)
            stream = urllib.urlopen(url, data)
        else:
            arglist = []
            for key, value in kwargs.items():
                arglist.append("%s=%s" % (urllib.quote(key), urllib.quote(value)))
            if arglist:
                url += "?" + "&".join(arglist)
            stream = urllib.urlopen(url)
        status = stream.getcode()
        output = "\n".join(stream.readlines())
        self.assertEqual(status, expect_status,
                         "HTTP status code for %s (%s) was %d instead of %d"
                         "\nOutput was:\n@@@\n%s\n@@@\n"
                         % (path, repr(kwargs), status, expect_status, output))
        return output

    def badrequesttest(self, path, **kwargs):
        return self.urltest(path, 400, **kwargs)

    def testintarg1(self):
        # search cpu --speed not-a-number
        path = "/find/hardware/cpu"
        out = self.badrequesttest(path, speed="not-a-number")
        self.matchoutput(out, "Expected an integer for --speed.", path)

    def testintarg2(self):
        # search machine --cpucount not-a-number
        path = "/find/machine"
        out = self.badrequesttest(path, cpucount="not-a-number")
        self.matchoutput(out, "Expected an integer for --cpucount.", path)

    def testboolarg(self):
        # search host --all
        path = "/host"
        out = self.badrequesttest(path, all="not-a-bool")
        self.matchoutput(out, "Expected a boolean value for --all.", path)

    # Can't test this here because the permission check happens first,
    # and update_personality will not work unauthenticated.
    # Thus there is no coverage on this block of broker code, as the
    # client will catch the error first.
    # If we ever have a search command that takes a float, that should
    # be used here.
#   def testfloatarg(self):
#       # update personality
#       path = "/personality/vmhost/esx_desktop"
#       out = self.badrequesttest(path, post=True, archetype="vmhost",
#                                 personality="esx_desktop",
#                                 vmhost_overcommit_memory="not-a-float")
#       self.matchoutput(out, "Expected an floating point", path)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClientBypass)
    unittest.TextTestRunner(verbosity=2).run(suite)
