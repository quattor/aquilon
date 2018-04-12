#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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


class DSDB(object):
    """
    DSDB Interface class
    demonstrating datastructures and methods
    that DSDB class provides.
    Used if no DSDB module imported.
    """

    def __init__(self, plant='test', debug=True):
        pass

    def show_rack(self, rack_name):
        return DSDBRackData(rack_name)

    def add_rack(self, id, building, floor, comp_room, row, column, comments=None):
        rack_name = building+id
        dsdb_racks = DSDBRackData(rack_name)
        if dsdb_racks.results() or rack_name in dsdb_racks.side_effect:
            raise Exception('Rack {} is already defined'.format(rack_name))

    def delete_rack(self, rack_name):
        dsdb_racks = DSDBRackData(rack_name)
        if rack_name in dsdb_racks.side_effect:
            raise Exception('Delete from DSDB failed!')

    def update_rack(self, rack, **kwargs):
        dsdb_racks = DSDBRackData(rack)
        if rack in dsdb_racks.side_effect:
            raise Exception('Update in DSDB failed!')


class DSDBRackData(object):
    """
    DSDB Rack Data Description
    used by DSDB Interface class
    if no DSDB module loaded
    """
    dsdb_host_data = {"oy604": [{u'comp_room': u'103',
                                 u'floor': u'1', u'column': u'04',
                                 u'comments': u'rrackspyid:3163',
                                 u'chassis': [u'oy604c1', u'oy604c2'],
                                 u'rack_name': u'oy604', u'row': u'B',
                                 u'building_name': u'oy'}],
                      }
    side_effect = ["ut666", "oy604"]

    def __init__(self, rack_name):
        self.rack_name = rack_name

    def results(self):
        return self.dsdb_host_data.get(self.rack_name, [])
