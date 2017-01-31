#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015,2016,2017  Contributor
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

import os, os.path
import sys
import logging
from optparse import OptionParser

BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(os.path.join(BINDIR, "..", "..", "lib"))

import aquilon.aqdb.depends
import aquilon.worker.depends

from sqlalchemy.orm import joinedload, subqueryload

from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model import (Base, PersonalityStage, PersonalityParameter,
                                ParamDefHolder, ArchetypeParamDef)
from aquilon.worker.templates import Plenary, PlenaryCollection


def main():
    parser = OptionParser()
    parser.add_option("--commit", dest="commit", action="store_true",
                      default=False, help="Commit the changes made")
    parser.add_option("--debug", dest="debug", action="store_true",
                      default=False, help="Display SQL statements")
    opts, _ = parser.parse_args()

    db = DbFactory()
    if opts.debug:
        db.engine.echo = True
    Base.metadata.bind = db.engine

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("clean_parameters")
    plenaries = PlenaryCollection(logger=logger)

    session = db.Session()

    print "Using database:", str(db.engine.url)

    # Cache warmup
    q = session.query(PersonalityStage)
    q = q.options(joinedload('personality'))
    personalities = q.all()

    # Cache warmup
    q = session.query(ParamDefHolder)
    q = q.with_polymorphic('*')
    q = q.options(subqueryload('param_definitions'))
    holders = q.all()

    # This is not very efficient, but more portable than trying to filter on a
    # LOB column
    count = 0
    q = session.query(PersonalityParameter)
    for dbparam in q:
        if not dbparam.value:
            if isinstance(dbparam.param_def_holder, ArchetypeParamDef):
                plenaries.append(Plenary.get_plenary(dbparam))
            session.delete(dbparam)
            count += 1

    print "Deleted %d empty parameter objects." % count
    print "Flushing changes to the database..."

    session.flush()
    plenaries.stash()

    if opts.commit:
        with plenaries.transaction():
            session.commit()
    else:
        print "**** WARNING ****"
        print "The --commit option was not specified, changes are not persisted."
        session.rollback()
        plenaries.restore_stash()

if __name__ == '__main__':
    main()
