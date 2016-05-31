#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015,2016  Contributor
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
from aquilon.aqdb.model import (Base, ParamDefinition, ArchetypeParamDef,
                                PersonalityParameter, PersonalityStage,
                                Archetype, Feature)


def clean_params(dbstage):
    link_by_defholder = defaultdict(list)
    print format(dbstage)
    for link in dbstage.archetype.features + dbstage.features:
        defholder = link.feature.param_def_holder
        if defholder not in dbstage.parameters:
            continue
        link_by_defholder[defholder].append(link)

    for defholder, links in link_by_defholder.items():
        param = dbstage.parameters[defholder]
        new_param = PersonalityParameter(value={})
        print "  Feature: %s" % defholder.feature
        for paramdef in defholder.param_definitions:
            path = paramdef.path
            for dblink in links:
                value = param.get_path(dblink.feature.cfg_path + "/" + path, compel=False)
                if value is not None:
                    new_param.set_path(path, value)
        print "  --> Old: %r" % param.value
        print "  --> New: %r" % new_param.value
        param.value = new_param.value

    for param_def_holder in dbstage.archetype.param_def_holders.values():
        if param_def_holder not in dbstage.parameters:
            continue

        print "  Template: %s" % param_def_holder.template
        param = dbstage.parameters[param_def_holder]
        new_param = PersonalityParameter(value={})
        for paramdef in param_def_holder.param_definitions:
            path = param_def_holder.template + "/" + paramdef.path
            value = param.get_path(path, compel=False)
            if value is not None:
                new_param.set_path(paramdef.path, value)
        print "  --> Old: %r" % param.value
        print "  --> New: %r" % new_param.value
        param.value = new_param.value


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

    print "Using database:", str(db.engine.url)

    q = session.query(Feature)
    q = q.options(joinedload('param_def_holder'),
                  subqueryload('param_def_holder.param_definitions'))
    features = q.all()

    q = session.query(Archetype)
    q = q.options(joinedload('param_def_holders'),
                  subqueryload('param_def_holders.param_definitions'),
                  subqueryload('features'))
    archetypes = q.all()

    #dbstage = Personality.get_unique(session, name="unixeng-test").stages["current"]
    #with session.no_autoflush:
    #    clean_params(dbstage)

    with session.no_autoflush:
        q = session.query(ParamDefinition)
        q = q.join(ParamDefinition.holder.of_type(ArchetypeParamDef))
        for paramdef in q:
            if "/" in paramdef.path:
                _, new_path = paramdef.path.split("/", 1)
                paramdef.path = new_path
            else:
                paramdef.path = ""

        q = session.query(PersonalityStage)
        q = q.options(joinedload('personality'),
                      subqueryload('features'),
                      subqueryload('parameters'))

        for dbstage in q:
            clean_params(dbstage)

    print "Flushing changes to the database..."

    session.flush()

    if opts.commit:
        session.commit()
    else:
        print "**** WARNING ****"
        print "The --commit option was not specified, changes are not persisted."
        session.rollback()

if __name__ == '__main__':
    main()
