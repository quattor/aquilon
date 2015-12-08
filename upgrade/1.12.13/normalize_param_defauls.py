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
import os, os.path
import sys
import logging
import json
from optparse import OptionParser

BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(os.path.join(BINDIR, "..", "..", "lib"))

import aquilon.aqdb.depends  # pylint: disable=W0611
import aquilon.worker.depends  # pylint: disable=W0611

from sqlalchemy.orm import subqueryload
from sqlalchemy.sql import null

from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model import Base, ParamDefinition


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

    session = db.Session()

    print("Using database:", str(db.engine.url))

    cnt = 0

    q = session.query(ParamDefinition)
    q = q.filter_by(value_type="json")
    q = q.filter(ParamDefinition.default != null())
    q = q.options(subqueryload("holder"))
    for db_paramdef in q:
        old_default = db_paramdef.default
        new_default = json.dumps(json.loads(old_default), sort_keys=True)
        if new_default != db_paramdef.default:
            print("Updating {0} of {0.holder.holder_object:l}")
            print("  --> Old: %s" % old_default)
            print("  --> New: %s" % new_default)
            db_paramdef.default = new_default
            cnt += 1

    print("Flushing changes")

    session.flush()

    print("Checked %d, converted %d parameters." % (q.count(), cnt))

    if opts.commit:
        session.commit()
    else:
        if cnt:
            print("*** WARNING ***")
            print("The --commit option was not specified, rolling back.")
        session.rollback()

if __name__ == '__main__':
    main()
