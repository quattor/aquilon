#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2019  Contributor
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
"""Module for testing the del shared service name command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelSharedServiceName(TestBrokerCommand):

    def test_000_no_pn_cluster(self):
        # ensure we cannot delete a shared service name from a cluster
        command = ['del_shared_service_name', '--cluster=utvcs1',
                   '--name=utvcs1pn1']
        err = self.badoptiontest(command)
        self.matchoutput(err, 'no such option: --cluster', command)

    def test_000_no_pn_host(self):
        # ensure we cannot delete a shared service name from a host
        command = ['del_shared_service_name',
                   '--hostname=evh83.aqd-unittest.ms.com',
                   '--name=utvcs1pn1']
        err = self.badoptiontest(command)
        self.matchoutput(err, 'no such option: --hostname', command)

    def test_200_pn_del(self):
        # remove first shared-service-name
        command = ['del_shared_service_name', '--resourcegroup=utvcs1ifset',
                   '--name=utvcs1pn1']
        self.successtest(command)

    def test_200_pn_del2(self):
        # remove second shared-service-name
        command = ['del_shared_service_name', '--resourcegroup=utvcs1ifset2',
                   '--name=utvcs1pn2']
        self.successtest(command)

    def test_210_rg_del(self):
        # remove first specific resourcegroup (should be empty)
        command = ['del_resourcegroup', '--resourcegroup=utvcs1ifset',
                   '--cluster=utvcs1']
        self.successtest(command)

    def test_210_rg_del2(self):
        # remove second specific resourcegroup (should be empty)
        command = ['del_resourcegroup', '--resourcegroup=utvcs1ifset2',
                   '--cluster=utvcs1']
        self.successtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
                TestDelSharedServiceName)
    unittest.TextTestRunner(verbosity=2).run(suite)
