#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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

import logging
import os
from shutil import rmtree

from aquilon.consistency.checker import ConsistencyChecker
from aquilon.aqdb.model.branch import Domain
from aquilon.worker.processes import run_git


class DomainChecker(ConsistencyChecker):
    """Domain Consistency Checker"""

    def check_single_domain(self, dbdomain, repair=False):
        domaindir = os.path.join(self.config.get("broker", "domainsdir"),
                                 dbdomain.name)
        if not os.path.exists(domaindir):
            if repair:
                kingdir = self.config.get("broker", "kingdir")
                self.logger.info("Checking out {0:l}".format(dbdomain))
                run_git(["clone", "--quiet", "--branch", dbdomain.name, kingdir,
                         domaindir], loglevel=logging.DEBUG)
            else:
                self.failure(dbdomain.name, format(dbdomain),
                             "found in the database but not on the "
                             "filesystem (%s)" % domaindir)
                return

    def check(self, repair=False):
        db_domains = {}
        for domain in self.session.query(Domain):
            db_domains[domain.name] = domain
            self.check_single_domain(domain, repair=repair)

        # Find all of the domains
        fs_domains = set()
        fsinfo = {}
        domainsdir = self.config.get("broker", "domainsdir")
        for (root, dirs, files) in os.walk(domainsdir):
            if files:
                self.failure(1, "Domains dir", "%s contains files" % root)
            for dir in dirs:
                fs_domains.add(dir)
                fsinfo[dir] = os.path.join(root, dir)
            # Prevent any further recursion
            dirs[:] = []

        #######################################################################
        #
        # Database (domains) == Filesystem (domains)
        #

        # Branches on filesystem but not in the database
        for branch in fs_domains.difference(db_domains.keys()):
            if repair:
                self.logger.info("Removing %s", fsinfo[branch])
                rmtree(fsinfo[branch])
            else:
                self.failure(branch, "Domain %s" % branch,
                             "found on the filesystem (%s) but not in the "
                             "database" % fsinfo[branch])
