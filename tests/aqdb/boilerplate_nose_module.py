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
""" DESCRIBE ME """
import logging
log = logging.getLogger('nose.plugins.aqdb')

from utils import load_classpath, add, commit, create, func_name
load_classpath()

from aquilon.aqdb.db_factory import DbFactory
#from aquilon.aqdb.model import SOMETHING

#from nose.tools import raises, eq_

db = DbFactory()
sess = db.Session()

def setup():
    pass

def teardown():
    pass


if __name__ == "__main__":
    import nose
    nose.runmodule()
