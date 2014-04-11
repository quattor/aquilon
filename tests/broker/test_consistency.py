#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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

import os
import sys
from subprocess import Popen, PIPE

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestConsistency(TestBrokerCommand):

    def test_consistency(self):
        # Create a dummy domain directory, not in the database!
        dummydomain = os.path.join(self.config.get("broker", "domainsdir"),
                                   'dummydomain')
        try:
            os.mkdir(dummydomain)
        except OSError, e:
            # Directory may already exist
            pass

        # Run the checker and collect its output
        command = 'aqd_consistency_check.py'
        dir = os.path.dirname(os.path.realpath(__file__))
        checker = os.path.join(dir, '..', '..', 'sbin', command)
        env = os.environ.copy()
        env['AQDCONF'] = self.config.baseconfig
        (out, err) = Popen(checker, stdout=PIPE, stderr=PIPE, env=env).communicate()
        self.assertEmptyErr(err, command)

        ########## Database (domains+sandbox's) == Git (domains+sandbox's)

        # "Domain XXXX found in database and not template-king"
        # The break-consistency-domain branch was added directly to the database
        # at the start of the unit test.  Unlike the prod domain, it
        # will not be in template-king.
        self.matchoutput(out, "Domain break-consistency-domain found in database "
                         "and not template-king", command)
        self.matchoutput(out, "Sandbox break-consistency-sandbox found in database "
                         "and not template-king", command)
        self.matchclean(out, "Domain prod found in database "
                         "and not template-king", command)

        # "Branch XXXX found in template-king and not database"
        # There will be a whole pile of these errors because we cloned
        # the template-king as part of the unit test system.
        self.matchoutput(out, 'found in template-king and not database',
                         command)
        self.matchclean(out, 'Domain prod found in template-king '
                        'and not database', command)

        ########## Database (sandbox) == Filesystem (sandbox)

        # "Sandbox XXXX found in database but not on filesystem"
        # The break-consistency-sandbox branch was added directly to the database
        # at the start of the unit test.  Unlike the prod domain, it
        # will not be found on the filing system.
        self.matchoutput(out, "Sandbox break-consistency-sandbox found in database "
                         "but not on filesystem", command)
        self.matchclean(out, "Sandbox managetest1 found in database "
                         "but not on filesystem", command)

        ########## Database (domains) == Filesystem (domains)

        # "Branch XXXX found in database but not on fileing system"
        # The break-consistency-domain is added to the database at the start
        # of the  unit test; however, it is created directly in the database
        # and not through the broker.  Hence why this is not found on the
        # filing system.
        self.matchoutput(out, "Domain break-consistency-domain found in database "
                         "but not on filesystem", command)
        self.matchclean(out, "Domain prod found in database "
                         "but not on filesystem", command)

        # "Domain XXXX found on filesystem (%s) but not in database"
        # We created a dummy path at the beginning of this test, as a result
        # it's not represented in the database.
        self.matchoutput(out, "Domain dummydomain found on filesystem (%s) "
                         "but not in database" % dummydomain,
                         command)
        self.matchclean(out, "Domain prod found on filesystem",
                        command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConsistency)
    unittest.TextTestRunner(verbosity=2).run(suite)
