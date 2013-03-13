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
""" Routines to query information about NAS shares """

from aquilon.config import Config

# Utility functions for service / resource based disk mounts
# This should come from some external API...?
def cache_storage_data():
    """
    Scan a storeng-style data file, checking each line as we go

    Storeng-style data files are blocks of data. Each block starts
    with a comment describing the fields for all subsequent lines. A
    block can start at any time. Fields are separated by '|'.
    This function will invoke the function after parsing every data
    line. The function will be called with a dict of the fields. If the
    function returns True, then we stop scanning the file, else we continue
    on until there is nothing left to parse.

    dbshare can be a Share
    """

    config = Config()
    sharedata = {}
    with open(config.get("broker", "sharedata")) as datafile:
        def process_nas_line(info):
            # silently discard lines that don't have all of our reqd info.
            for k in ["objtype", "pshare", "server", "dg"]:
                if k not in info:
                    return

            if info["objtype"] != "pshare":
                return

            sharedata[info["pshare"]] = {
                "server": info["server"],
                "mount": "/vol/%s/%s" % (info["dg"], info["pshare"]),
            }

        for line in datafile:
            line = line.rstrip()

            if line[0] == '#':
                # A header line
                hdr = line[1:].split('|')
            else:
                fields = line.split('|')
                if len(fields) != len(hdr):  # silently ignore invalid lines
                    continue

                info = dict()
                for i in range(0, len(hdr)):
                    info[hdr[i]] = fields[i]

                process_nas_line(info)

        return sharedata


def find_storage_data(dbshare, cache=None):
    if not cache:
        cache = cache_storage_data()
    if dbshare.name in cache:
        return cache[dbshare.name]
    else:
        return {"server": None, "mount": None}
