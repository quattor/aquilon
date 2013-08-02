#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2013  Contributor
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
Populate location link table with locations links and hop distance.
"""

import os
import sys

BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(os.path.join(BINDIR, "..", "..", "lib", "python2.6"))

import aquilon.aqdb.depends
from aquilon.config import Config

from aquilon.aqdb.model import Base
from aquilon.aqdb.db_factory import DbFactory

db = DbFactory()

LINK_INS = "insert into location_link (child_id,parent_id,distance) values (:cid,:pid,:dist) "
SELECT = """select id,name,parent_id,location_type from location """
Base.metadata.bind = db.engine

session = db.Session()

def get_dict():
    """ build a hash of location data keyed on  id"""
    result = db.engine.execute(SELECT)
    ldict = {}
    for item in result:
        ldict[item[0]] = {'name':item[1], 'pid':item[2], 'type':item[3]}
    return ldict

def main():
    """ build location links from each location traversing
        thru the parent """
    ldict = get_dict()
    for curr_id in ldict.keys():
        child_id = curr_id
        child = ldict[curr_id]
        print "Processing ", child_id, child
        parent_id = child['pid']
        dist = 0
        while parent_id is not None:
            dist = dist +1
            parent = ldict[parent_id]
            print ("Adding child [%s/%s = %d], parent [%s/%s =%d], dist=%d"
                  % (child['type'], child['name'], child_id, parent['type'],
                     parent['name'], parent_id, dist))
            db.engine.execute(LINK_INS, {'cid' : child_id, 'pid' : parent_id, 'dist' : dist})
            parent_id = parent['pid']

    session.commit()

if __name__ == '__main__':
    main()
