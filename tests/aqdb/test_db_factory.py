#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
""" test the mock engine feature """

import os
import sys


_DIR = os.path.dirname(os.path.realpath(__file__))
_LIBDIR = os.path.join(_DIR, "..", "..", "lib")
sys.path.insert(0, _LIBDIR)

from aquilon.aqdb.db_factory import DbFactory

db = None

def test_init():
    db = DbFactory()
    assert db, 'No db factory created'

#would test singleton functionality
__sql = """
  SELECT substr(a.spid,1,9) pid,
         substr(b.sid,1,5) sid,
         substr(b.serial#,1,5) ser#,
         substr(b.machine,1,6) box,
         substr(b.username,1,10) username,
         substr(b.osuser,1,8) os_user,
         substr(b.program,1,30) program
  FROM v$session b, v$process a
  WHERE b.paddr  = a.addr and type='USER'
  AND b.username = 'SATEST'
  ORDER BY spid;

  exit;

"""
