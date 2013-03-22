#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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
"""
Add start points for existing sandboxes
"""

import os, os.path
import sys
import logging

BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(os.path.join(BINDIR, "..", "..", "lib", "python2.6"))

import aquilon.aqdb.depends
import aquilon.worker.depends
from aquilon.config import Config

from sqlalchemy.orm import defer
from sqlalchemy.sql import text
from sqlalchemy.exc import DatabaseError

from aquilon.aqdb.model import Base, Sandbox, Domain
from aquilon.aqdb.db_factory import DbFactory
from aquilon.worker.processes import run_git

db = DbFactory()
Base.metadata.bind = db.engine

session = db.Session()
config = Config()


def main():
    print "Calculating sandbox base commits. This may take around 10 minutes."

    logging.basicConfig(level=logging.WARNING)
    kingdir = config.get("broker", "kingdir")

    domains = session.query(Domain).all()

    # Define preference order when multiple domains have the same commits.
    # This is just cosmetics, but makes it easier to verify the output.
    for idx, domain in enumerate(("prod", "qa", "secure-aquilon-prod",
                                  "secure-aquilon-qa")):
        dbdom = Domain.get_unique(session, domain, compel=True)
        domains.remove(dbdom)
        domains.insert(idx, dbdom)

    base_commits = {}
    q = session.query(Sandbox)
    q = q.order_by('name')

    # The base_commit column does not exist yet...
    q = q.options(defer("base_commit"))

    for sandbox in q:
        base_domain = None
        base_commit = None
        min_ahead = None

        commits = run_git(["rev-list", "refs/heads/" + sandbox.name], path=kingdir).split("\n")

        for domain in domains:
            merge_base = run_git(["merge-base", "refs/heads/" + sandbox.name,
                                  "refs/heads/" + domain.name],
                                 path=kingdir).strip()
            # Number of commits since branching from the given domain
            ahead = commits.index(merge_base)

            if base_domain is None or ahead < min_ahead:
                base_domain = domain
                base_commit = merge_base
                min_ahead = ahead

            if min_ahead == 0:
                break

        print "{0: <40}: {1.name} (ahead {2})".format(sandbox, base_domain,
                                                      min_ahead)

        base_commits[sandbox.name] = base_commit

    session.expunge_all()

    try:
        if session.bind.dialect.name == 'oracle':
            query = text("""
        ALTER TABLE sandbox ADD base_commit VARCHAR2(40 CHAR)
""")
        elif session.bind.dialect.name == 'postgresql':
            query = text("""
        ALTER TABLE sandbox ADD base_commit CHARACTER VARYING (40)
""")
        print "\nExecuting: %s" % query
        session.execute(query)
        session.commit()
    except DatabaseError:
        # Allow the script to be re-run by not failing if the column already
        # exists. If the column does not exist, then trying to update it will
        # fail anyway.
        print """
WARNING: Adding the sandbox.base_commit column has failed. If you're running
this script for the second time, then that's likely OK, otherwise you should
verify and correct the schema manually.
"""
        session.rollback()

    for sandbox in q:
        sandbox.base_commit = base_commits[sandbox.name]
    session.commit()

    try:
        if session.bind.dialect.name == 'oracle':
            query = text("""
        ALTER TABLE sandbox MODIFY (base_commit VARCHAR2(40 CHAR)
            CONSTRAINT sandbox_base_commit_nn NOT NULL)
""")
        elif session.bind.dialect.name == 'postgresql':
            query = text("""
        ALTER TABLE sandbox ALTER COLUMN base_commit SET NOT NULL
""")
        print "\nExecuting: %s" % query
        session.execute(query)
        session.commit()
    except DatabaseError:
        print """
WARNING: Enabling the NOT NULL constraint for sandbox.base_commit column has
failed. If you're running this script for the second time, then that's likely
OK, otherwise you should verify and correct the schema manually.
"""
        session.rollback()

if __name__ == '__main__':
    main()
