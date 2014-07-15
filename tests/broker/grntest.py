# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
""" Helper classes for GRN testing """

import os
from csv import DictReader


class VerifyGrnsMixin(object):

    def setUp(self):
        super(VerifyGrnsMixin, self).setUp()

        if hasattr(self, "grns"):
            return

        self.grns = {}
        self.eon_ids = {}
        dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir, "..", "fakebin", "eon-data",
                               "eon_catalog.csv")) as f:
            reader = DictReader(f)
            for row in reader:
                self.grns[row["name"]] = int(row["id"])
                self.eon_ids[int(row["id"])] = row["name"]

    def check_grns(self, out, grn_list, grn_maps, command):
        def check_grn_for_key(grn_list, key):
            eon_ids = sorted(self.grns[grn] for grn in grn_list)
            self.searchoutput(out,
                              r'"%s" = list\(\s*' % key +
                              r',\s*'.join([str(eon_id) for eon_id in eon_ids]) +
                              r'\s*\);',
                              command)

        check_grn_for_key(grn_list, "system/eon_ids")
        for (target, target_list) in grn_maps.iteritems():
            check_grn_for_key(target_list, "system/eon_id_maps/%s" % target)

    def check_personality_grns(self, out, grn_list, grn_maps, command):
        def check_grn_for_key(grn_list, key):
            eon_ids = sorted(self.grns[grn] for grn in grn_list)
            for eon_id in eon_ids:
                self.searchoutput(out,
                                  r'"%s" = append\(%d\);' % (key, eon_id),
                                  command)

        check_grn_for_key(grn_list, "/system/eon_ids")
        for (target, target_list) in grn_maps.iteritems():
            check_grn_for_key(target_list, "/system/eon_id_maps/%s" % target)
