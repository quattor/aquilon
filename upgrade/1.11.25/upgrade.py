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
"""
Reconfigure hosts affected by the resource path changes
"""

import os, os.path
import sys
import logging

BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(os.path.join(BINDIR, "..", "..", "lib"))

import aquilon.aqdb.depends
import aquilon.worker.depends
from aquilon.config import Config

from aquilon.aqdb.db_factory import DbFactory
from aquilon.worker.logger import RequestLogger
from aquilon.aqdb.model import (Base, Archetype, HostLifecycle, NetworkDevice,
                                Personality, OperatingSystem, Host)
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.branch import get_branch_and_author


db = DbFactory()
Base.metadata.bind = db.engine

logging.basicConfig(level=logging.DEBUG)
module_logger = logging.getLogger(__name__)

session = db.Session()
logger = RequestLogger(module_logger=module_logger)
config = Config()

def main():
    print "Using database:", db.dsn

    archetype='netinfra'
    domain='netinfra'
    grn='grn:/ms/ei/network/tools/NetManSystems'

    buildstatus='build'
    personality = 'generic'
    osname = 'generic'
    osversion = 'generic'

    ## Archetype
    dbarchetype = Archetype.get_unique(session, archetype, compel=True)

    ## branch/sandbox_author
    (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                 domain=domain,
                                                 compel=True)

    ## Lifecycle
    dbstatus = HostLifecycle.get_instance(session, buildstatus)

    ## Personality
    dbpersonality = Personality.get_unique(session, name=personality,
                                           archetype=dbarchetype,
                                           compel=True)

    ## Operating system
    dbos = OperatingSystem.get_unique(session, name=osname,
                                      version=osversion,
                                      archetype=dbarchetype, compel=True)

    ## Lookup GRN's
    dbgrn = lookup_grn(session, grn, logger=logger,
                       config=config)

    ##### Process all existing network devices

    count_success = 0
    count_failed = 0
    q = session.query(NetworkDevice)
    for dbnetdev in q.all():
        print 'Processing', dbnetdev.label, '...',
        try:
            dbhost = Host(hardware_entity=dbnetdev, branch=dbbranch,
                          owner_grn=dbgrn, sandbox_author=dbauthor,
                          personality=dbpersonality, status=dbstatus,
                          operating_system=dbos)
            session.add(dbhost)
            print 'DONE'
            count_success = count_success + 1
        except Exception, e:
            print 'FAILED'
            print e
            count_failed = count_failed + 1

    if count_failed == 0:
        print 'Commiting', count_success, 'entries'
        session.flush()
        session.commit()
    else:
        print 'Aborting, there were', count_failed, 'failed entries'

if __name__ == '__main__':
    main()
