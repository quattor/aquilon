#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
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
