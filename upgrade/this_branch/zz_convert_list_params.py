#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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

from __future__ import print_function
from collections import defaultdict
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
from aquilon.aqdb.model import (Base, Parameter, PersonalityParameter,
                                PersonalityStage, Archetype, Feature)


def clean_params(dbstage):
    if not dbstage.parameter:
        return 0

    features = set(link.feature for link in
                   dbstage.archetype.features + dbstage.features)

    param = dbstage.parameter
    new_param = PersonalityParameter(value={})

    for dbfeature in features:
        defholder = dbfeature.param_def_holder
        if not defholder:
            continue

        for paramdef in defholder.param_definitions:
            path = Parameter.feature_path(dbfeature, paramdef.path)
            value = param.get_path(path, compel=False)
            if value is not None:
                if paramdef.value_type == "list":
                    value = [item.strip() for item in value.split(",")]
                new_param.set_path(path, value, preclude=True)

    for param_def_holder in dbstage.archetype.param_def_holders.values():
        for paramdef in param_def_holder.param_definitions:
            value = param.get_path(paramdef.path, compel=False)
            if value is not None:
                if paramdef.value_type == "list":
                    value = [item.strip() for item in value.split(",")]
                new_param.set_path(paramdef.path, value, preclude=True)

    if param.value != new_param.value:
        print(format(dbstage))
        print("  --> Old: %r" % param.value)
        print("  --> New: %r" % new_param.value)
        param.value = new_param.value
        return 1
    else:
        return 0


def main():
    parser = OptionParser()
    parser.add_option("--commit", dest="commit", action="store_true",
                      default=False, help="Commit the changes made")
    parser.add_option("--debug", dest="debug", action="store_true",
                      default=False, help="Display SQL statements")
    opts, args = parser.parse_args()

    db = DbFactory()
    if opts.debug:
        db.engine.echo = True
    Base.metadata.bind = db.engine

    logging.basicConfig(level=logging.DEBUG)

    session = db.Session()

    print("Using database:", str(db.engine.url))

    q = session.query(Feature)
    q = q.options(joinedload('param_def_holder'),
                  subqueryload('param_def_holder.param_definitions'))
    features = q.all()

    q = session.query(Archetype)
    q = q.options(joinedload('param_def_holders'),
                  subqueryload('param_def_holders.param_definitions'),
                  subqueryload('features'))
    archetypes = q.all()

    q = session.query(PersonalityStage)
    q = q.options(joinedload('personality'),
                  subqueryload('features'),
                  joinedload('parameter'))

    cnt = 0
    with session.no_autoflush:
        for dbstage in q:
            cnt += clean_params(dbstage)

    print("Flushing changes")

    session.flush()

    print("Checked %d, converted %d parameters." % (q.count(), cnt))

    if opts.commit:
        session.commit()
    else:
        print("*** WARNING ***")
        print("The --commit option was not specified, rolling back.")
        session.rollback()

if __name__ == '__main__':
    main()
