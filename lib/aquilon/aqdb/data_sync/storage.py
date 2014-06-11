# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
""" Routines to query information about NAS shares """

from collections import namedtuple
from operator import itemgetter
import re

import cdb

from aquilon.config import Config

DataBlock = namedtuple('DataBlock', ['start_index', 'columns'])
ShareInfo = namedtuple('ShareInfo', ['server', 'mount'])


class StormapParser(object):
    """
    Scan a storeng-style CDB data file.

    Storeng-style data files are blocks of data. Each block has a header
    describing the fields for all subsequent lines. A block can start at any
    time. Fields are separated by '|'.

    The CDB file contains one row per line of the original text dump, where the
    key is the line number and the value is the line contents. The cdb file also
    contains a number of indexes to make lookups faster. There is metadata
    describing the number of maps, the columns in any given map, and the line
    number range for that map.
    """

    row_key_re = re.compile(r"D:(\d+)$")

    def __init__(self):
        config = Config()
        self.header_defs = []

        # TODO: This code can be used to parse other data files with the same
        # format. To do that, we'll need to pass the file name as an argument to
        # __init__(), and the index type as an argument to lookup().
        self.cdb_file = cdb.init(config.get("broker", "sharedata"))
        num_headers = self.cdb_file["M:HEADER_COUNT"]
        if num_headers is None:
            return

        for header_num in range(0, int(num_headers)):
            # Index of the first item the header refers to
            start_index = int(self.cdb_file["HEADER_ROW_INDEX:%d" % header_num])
            # Definitions for the fields in the given segment
            header = self.cdb_file["HEADER_ROW_COLUMN_NAMES:%d" % header_num]
            if not header:
                continue

            columns = dict((name, idx) for idx, name in
                           enumerate(header.split('|')))
            self.header_defs.append(DataBlock(start_index=start_index,
                                              columns=columns))

        # Guard element - if a row index is out of range, this will catch it
        self.header_defs.append(DataBlock(start_index=int(self.cdb_file["M:ROW_COUNT"]),
                                          columns={}))

        # We need to sort the definitions to be able to find the range a given
        # line falls into. The trick here is that we know that the items we're
        # currently interested in should be part of the last range, so sorting
        # in descending order will make lookups faster.
        self.header_defs.sort(key=itemgetter(0), reverse=True)

    def lookup(self, name):
        try:
            # Look up the name in the index...
            row_key = self.cdb_file["I:pshare:" + str(name)]
            # ... and the row containing the data
            row = self.cdb_file[row_key]
        except KeyError:
            return ShareInfo(server=None, mount=None)

        # The key has the line number embedded, which we need to extract to be
        # able to figure out which header defines the structure of this row
        m = self.row_key_re.match(row_key)
        if not m:
            return ShareInfo(server=None, mount=None)
        row_index = int(m.group(1))

        # See the comment above about the ordering of self.header_defs - we're
        # depending on that here. The number of headers is expected to be small
        # enough, so linear search is more than adequate.
        headers = {}
        for start_index, headers in self.header_defs:
            if start_index <= row_index:
                break

        fields = row.split("|")

        # Final sanity checks
        if (not headers or len(fields) < len(headers) or
            "server" not in headers or
            "dg" not in headers or
            "pshare" not in headers):
            return ShareInfo(server=None, mount=None)

        return ShareInfo(server=fields[headers["server"]],
                         mount="/vol/%s/%s" % (fields[headers["dg"]],
                                               fields[headers["pshare"]]))
