#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Module for tests that bypass the aq client."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

from six.moves.urllib_parse import urlencode, quote  # pylint: disable=F0401
from six.moves.urllib_request import urlopen  # pylint: disable=F0401
from six.moves.urllib_error import HTTPError  # pylint: disable=F0401

import unittest2 as unittest
from brokertest import TestBrokerCommand


# This is a bit rough now. There are some error conditions (like syntax checks
# for integer options) that are done by both the broker and the client. Testing
# that the broker really does the checks requires us bypassing the client.
class TestClientBypass(TestBrokerCommand):

    def urltest(self, path, expect_status, post=False, **kwargs):
        openport = self.config.get("broker", "openport")
        server = self.config.get("broker", "servername")
        url = "http://" + server + ":" + openport + path
        try:
            if post:
                data = urlencode(kwargs)
                stream = urlopen(url, data)
            else:
                arglist = []
                for key, value in kwargs.items():
                    arglist.append("%s=%s" % (quote(key), quote(value)))
                if arglist:
                    url += "?" + "&".join(arglist)
                stream = urlopen(url)
            status = stream.getcode()
            output = stream.read()
        except HTTPError as err:
            status = err.code
            output = err.read()

        self.assertEqual(status, expect_status,
                         "HTTP status code for %s (%s) was %d instead of %d"
                         "\nOutput was:\n@@@\n%s\n@@@\n"
                         % (path, repr(kwargs), status, expect_status, output))
        return output

    def badrequesttest(self, path, **kwargs):
        return self.urltest(path, 400, **kwargs)

    def testintarg(self):
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
#       path = "/personality/vmhost/vulcan-10g-server-prod"
#       out = self.badrequesttest(path, post=True, archetype="vmhost",
#                                 personality="vulcan-10g-server-prod",
#                                 vmhost_overcommit_memory="not-a-float")
#       self.matchoutput(out, "Expected an floating point", path)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClientBypass)
    unittest.TextTestRunner(verbosity=2).run(suite)
