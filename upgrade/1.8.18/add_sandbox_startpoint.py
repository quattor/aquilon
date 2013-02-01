#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012  Contributor
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
