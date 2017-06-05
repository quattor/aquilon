#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013,2014  Contributor
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

from aquilon.exceptions_ import InternalError


class ConsistencyChecker(object):
    """Consistency Checker Base Class"""
    def __init__(self, config, session, logger):
        self.session = session
        self.config = config
        self.logger = logger
        self._failures = dict()

    def check(self, repair=False):  # pylint: disable=W0613
        """Perform the consistency check

        This method should be overridden to implement the class.
        """
        raise InternalError("The check method of %s is unimplemented" %
                            self.__class__.__name__)

    def failure(self, key, item, problem):
        """Record a failure

        Takes a string as a single argument.
        """
        if key not in self._failures:
            self._failures[key] = dict()
        if item not in self._failures[key]:
            self._failures[key][item] = list()
        self._failures[key][item].append(problem)

    def process_failures(self):
        """Process Failures for this checker

        This method prints out all of the failures that have occurred for this
        checker.  If there were no failures then True is returned, false
        otherwise.
        """
        for key in sorted(self._failures):
            for item in sorted(self._failures[key]):
                for problem in self._failures[key][item]:
                    print(item + ' ' + problem)
        if self._failures:
            return False
        return True
