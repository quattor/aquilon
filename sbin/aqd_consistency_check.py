#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "lib"))

import aquilon.aqdb.depends
import aquilon.worker.depends
from aquilon.consistency.checks import consistency_check_classes


success_flag = True
for checker_class in consistency_check_classes:
    checker = checker_class()
    checker.check()
    if not checker.process_failures():
        success_flag = False

if not success_flag:
    print "There were failuers"
    exit (1)

print "All tests passed successfully"
exit (0)
