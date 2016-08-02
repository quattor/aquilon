#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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

import argparse
import logging
import os
import sys

# -- begin path_setup --
import ms.version

BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
LIBDIR = os.path.join(BINDIR, "..", "lib")

if LIBDIR not in sys.path:
    sys.path.append(LIBDIR)
# -- end path_setup --

import aquilon.aqdb.depends  # pylint: disable=W0611
import aquilon.worker.depends  # pylint: disable=W0611
from aquilon.consistency.checks import consistency_check_classes
from aquilon.config import Config


def main():
    parser = argparse.ArgumentParser(description="AQDB consistency checker")
    parser.add_argument("-c", "--config", dest="config",
                        help="Location of the broker configuration file")
    parser.add_argument("--repair", action="store_true",
                        help="Fix issues when possible")
    parser.add_argument("--debug", action="store_true",
                        help="Turn on debug logs on stderr")
    parser.add_argument("--skip", help="Test classes to skip (comma separated)")
    parser.add_argument("--only", help="Run only these classes (comma separated)")
    opts = parser.parse_args()

    config = Config(configfile=opts.config)

    if opts.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level, stream=sys.stdout,
                        format='%(asctime)s [%(levelname)s] %(message)s')

    logger = logging.getLogger("aqd_consistency")

    # These modules must be imported after the configuration has been
    # initialized
    from aquilon.aqdb.db_factory import DbFactory

    db = DbFactory()
    session = db.Session()

    consistency_check_class_names = set(cls.__name__ for cls in
                                        consistency_check_classes)

    if opts.only:
        only = set(opts.only.split(","))
        for item in only:
            if item not in consistency_check_class_names:
                logger.error("Unknown class to run: %s", item)

        classes_to_run = [cls for cls in consistency_check_classes
                          if cls.__name__ in only]
    else:
        classes_to_run = consistency_check_classes

    if opts.skip:
        skip = set(opts.skip.split(","))
        for item in skip:
            if item not in consistency_check_class_names:
                logger.error("Unknown class to skip: %s", item)
        classes_to_run = [cls for cls in classes_to_run
                          if cls.__name__ not in skip]

    errors = []
    for checker_class in classes_to_run:
        checker = checker_class(config=config, session=session, logger=logger)
        checker.check(repair=opts.repair)
        if not checker.process_failures():
            errors.append(checker_class)

        if opts.repair:
            # FIXME: make DB-related errors non-fatal?
            session.commit()
        else:
            session.rollback()

    if errors:
        print("There were failuers")
        raise SystemExit(1)

    print("All tests passed successfully")

if __name__ == '__main__':
    main()
