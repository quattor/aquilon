# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
""" Helper classes for switch testing """

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

    def check_grns(self, out, grn_list, command):
        eon_ids = [self.grns[grn] for grn in grn_list]
        eon_ids.sort()
        self.searchoutput(out,
                          r'"system/eon_ids" = list\(\s*' +
                          r',\s*'.join([str(eon_id) for eon_id in eon_ids]) +
                          r'\s*\);',
                          command)

    def check_personality_grns(self, out, grn_list, command):
        eon_ids = [self.grns[grn] for grn in grn_list]
        eon_ids.sort()
        for eon_id in eon_ids:
            self.searchoutput(out,
                              r'"/system/eon_ids" = append\(%d\);' % eon_id,
                              command)
