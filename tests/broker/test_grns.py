#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Module for testing GRN support."""

import os
import sys
import unittest
from subprocess import Popen, PIPE

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestGrns(TestBrokerCommand):

    def test_100_add_test1(self):
        command = ["add", "grn", "--grn", "grn:/ms/test1", "--eon_id", "1",
                   "--disabled"]
        self.noouttest(command)

    def test_101_verify_test1(self):
        command = ["show", "grn", "--eon_id", "1"]
        out = self.commandtest(command)
        self.matchoutput(out, "GRN: grn:/ms/test1", command)
        self.matchoutput(out, "EON ID: 1", command)
        self.matchoutput(out, "Disabled: True", command)

    def test_110_add_test2(self):
        command = ["add", "grn", "--grn", "grn:/ms/test2", "--eon_id", "123456789"]
        self.noouttest(command)

    def test_111_verify_test2(self):
        command = ["show", "grn", "--grn", "grn:/ms/test2"]
        out = self.commandtest(command)
        self.matchoutput(out, "GRN: grn:/ms/test2", command)
        self.matchoutput(out, "EON ID: 123456789", command)
        self.matchoutput(out, "Disabled: False", command)

    def test_150_update(self):
        command = ["update", "grn", "--grn", "grn:/ms/test1", "--nodisabled",
                   "--rename_to", "grn:/ms/test3"]
        self.noouttest(command)

    def test_151_verify_update(self):
        command = ["show", "grn", "--eon_id", "1"]
        out = self.commandtest(command)
        self.matchoutput(out, "GRN: grn:/ms/test3", command)
        self.matchoutput(out, "EON ID: 1", command)
        self.matchoutput(out, "Disabled: False", command)

    def test_200_refresh(self):
        command = ["refresh", "grns"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Added 1, updated 1, deleted 1 GRNs.", command)

    def test_210_verify_test1_renamed(self):
        command = ["show", "grn", "--eon_id", "1"]
        out = self.commandtest(command)
        self.matchoutput(out, "GRN: grn:/ms/ei/aquilon", command)
        self.matchoutput(out, "EON ID: 1", command)
        self.matchoutput(out, "Disabled: True", command)

    def test_211_verify_aqd(self):
        command = ["show", "grn", "--grn", "grn:/ms/ei/aquilon/aqd"]
        out = self.commandtest(command)
        self.matchoutput(out, "EON ID: 2", command)
        self.matchoutput(out, "Disabled: False", command)

    def test_212_verify_test2_gone(self):
        command = ["show", "grn", "--grn", "grn:/ms/test2"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "GRN grn:/ms/test2 not found.", command)

    def test_220_show_missing_eonid(self):
        command = ["show", "grn", "--eon_id", "987654321"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "EON ID 987654321 not found.", command)

    def test_400_map_personality(self):
        command = ["map", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--personality", "compileserver"]
        (out, err) = self.successtest(command)

    def test_405_map_personality(self):
        command = ["map", "grn", "--grn", "grn:/example/cards",
                   "--personality", "compileserver"]
        out = self.successtest(command)

    def test_410_verify_personality(self):
        command = ["show", "personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.matchoutput(out, "GRN: grn:/ms/ei/aquilon/aqd", command)

        command = ["cat", "--archetype=aquilon", "--personality=compileserver"]
        out = self.commandtest(command)
        self.matchoutput(out, '"/system/eon_ids" = push(2);', command)
        self.matchoutput(out, '"/system/eon_ids" = push(4);', command)

    def test_420_verify_host(self):
        command = ["show", "host", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "GRN: grn:/ms/ei/aquilon/aqd", command)

    def test_430_map_host(self):
        command = ["map", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--hostname", "unittest12.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_431_map_host_again(self):
        scratchfile = self.writescratch("hostlist",
                                        "unittest12.aqd-unittest.ms.com")
        command = ["map", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--list", scratchfile]
        # TODO: should this throw an error?
        self.noouttest(command)

    def test_432_map_host_plus_pers(self):
        # The personality already includes the GRN
        command = ["map", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--hostname", "unittest00.one-nyp.ms.com"]
        self.noouttest(command)

    def test_440_search(self):
        command = ["search", "host", "--grn", "grn:/ms/ei/aquilon/aqd"]
        out = self.commandtest(command)
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest20.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest12.aqd-unittest.ms.com", command)

    def test_450_map_disabled(self):
        command = ["map", "grn", "--grn", "grn:/ms/ei/aquilon",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "GRN grn:/ms/ei/aquilon is not usable for new "
                         "systems.", command)

    def test_460_map_missing_eonid(self):
        command = ["map", "grn", "--eon_id", "987654321",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "EON ID 987654321 not found.", command)
        # The EON ID is not in the CDB file, so the CSV file should not be
        # parsed
        self.matchclean(out, "acquiring", command)

    def test_460_map_missing_grn(self):
        command = ["map", "grn", "--grn", "grn:/ms/no-such-grn",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "GRN grn:/ms/no-such-grn not found.", command)
        # The GRN is not in the CDB file, so the CSV file should not be
        # parsed
        self.matchclean(out, "acquiring", command)

    def test_500_verify_unittest00(self):
        command = ["cat", "--hostname", "unittest00.one-nyp.ms.com", "--data",
                   "--generate"]
        out = self.commandtest(command)
        # The GRN is mapped to both the host and the personality; verify it is
        # not duplicated. Should print out both the host mapped
        # personality mapped grns
        self.searchoutput(out, r'"/system/eon_ids" = list\(\s+2,\s+4\s+\);', command)

    def test_510_verify_unittest20(self):
        command = ["cat", "--hostname", "unittest20.aqd-unittest.ms.com", "--data",
                   "--generate"]
        out = self.commandtest(command)
        # The GRN is mapped to the personality only
        self.searchoutput(out, r'"/system/eon_ids" = list\(\s+2,\s+4\s+\);', command)

    def test_520_verify_unittest12(self):
        command = ["cat", "--hostname", "unittest12.aqd-unittest.ms.com", "--data",
                   "--generate"]
        out = self.commandtest(command)
        # The GRN is mapped to the host only
        self.searchoutput(out, r'"/system/eon_ids" = list\(\s+2\s+\);', command)

    def test_600_delete_used_byhost(self):
        command = ["del", "grn", "--grn", "grn:/ms/ei/aquilon/aqd"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "GRN grn:/ms/ei/aquilon/aqd is still mapped to "
                         "hosts, and cannot be deleted.", command)

    def test_610_delete_missing(self):
        command = ["del", "grn", "--eon_id", "987654321"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "EON ID 987654321 not found.", command)

    def test_620_unmap_unittest12(self):
        command = ["unmap", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--hostname", "unittest12.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_620_unmap_unittest00(self):
        command = ["unmap", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--hostname", "unittest00.one-nyp.ms.com"]
        self.noouttest(command)

    def test_621_verify_unittest12(self):
        command = ["show", "host", "--hostname", "unittest12.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "GRN", command)

    def test_622_verify_search(self):
        command = ["search", "host", "--grn", "grn:/ms/ei/aquilon/aqd"]
        out = self.commandtest(command)
        # unittest00 is still included due to its personality
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest20.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest12.aqd-unittest.ms.com", command)

    def test_625_unmap_host_again(self):
        scratchfile = self.writescratch("hostlist",
                                        "unittest12.aqd-unittest.ms.com")
        command = ["unmap", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--list", scratchfile]
        # TODO: should this throw an error?
        self.noouttest(command)

    def test_630_delete_used_bypers(self):
        command = ["del", "grn", "--grn", "grn:/ms/ei/aquilon/aqd"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "GRN grn:/ms/ei/aquilon/aqd is still mapped to "
                         "personalities, and cannot be deleted.", command)

    def test_640_unmap_personality(self):
        command = ["unmap", "grn", "--grn", "grn:/example/cards",
                   "--personality", "compileserver"]
        self.noouttest(command)

        command = ["cat", "--archetype", "aquilon",
                   "--personality", "compileserver"]
        out = self.commandtest(command)
        self.matchoutput(out, '"/system/eon_ids" = push(2);', command)
        self.searchclean(out, '"/system/eon_ids" = push(4);', command)

        command = ["unmap", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--personality", "compileserver"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "GRN grn:/ms/ei/aquilon/aqd is the last grn on "
                         "Personality aquilon/compileserver and cannot be removed", command)

    def test_650_delete(self):
        command = ["del", "grn", "--grn", "grn:/example"]
        self.noouttest(command)

    def test_700_verify_unittest00(self):
        command = ["cat", "--hostname", "unittest00.one-nyp.ms.com", "--data",
                   "--generate"]
        out = self.commandtest(command)
        # The GRN was mapped to both the host and the personality;
        self.searchoutput(out, r'"/system/eon_ids" = list\(\s+2\s+\);', command)

    def test_710_verify_unittest20(self):
        command = ["cat", "--hostname", "unittest20.aqd-unittest.ms.com", "--data",
                   "--generate"]
        out = self.commandtest(command)
        # The GRN was mapped to the personality only
        self.searchoutput(out, r'"/system/eon_ids" = list\(\s+2\s+\);', command)

    def test_720_verify_unittest12(self):
        command = ["cat", "--hostname", "unittest12.aqd-unittest.ms.com", "--data",
                   "--generate"]
        out = self.commandtest(command)
        # The GRN was mapped to the host only
        self.searchclean(out, r'"/system/eon_ids"', command)

    def test_730_fail_map_overlimitlist(self):
        user = self.config.get("unittest", "user")
        hostlimit = self.config.getint("broker", "map_grn_max_list_size")
        hosts = []
        for i in range(1,20):
            hosts.append("thishostdoesnotexist%d.aqd-unittest.ms.com\n" %i)
        scratchfile = self.writescratch("mapgrnlistlimit", "".join(hosts))
        command = ["map", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--list", scratchfile]
        out = self.badrequesttest(command)
        self.matchoutput(out,"The number of hosts in list {0:d} can not be more "
                         "than {1:d}".format(len(hosts), hostlimit), command)

    def test_740_fail_unmap_overlimitlist(self):
        user = self.config.get("unittest", "user")
        hostlimit = self.config.getint("broker", "unmap_grn_max_list_size")
        hosts = []
        for i in range(1,20):
            hosts.append("thishostdoesnotexist%d.aqd-unittest.ms.com\n" %i)
        scratchfile = self.writescratch("mapgrnlistlimit", "".join(hosts))
        command = ["unmap", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--list", scratchfile]
        out = self.badrequesttest(command)
        self.matchoutput(out,"The number of hosts in list {0:d} can not be more "
                         "than {1:d}".format(len(hosts), hostlimit), command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGrns)
    unittest.TextTestRunner(verbosity=2).run(suite)
