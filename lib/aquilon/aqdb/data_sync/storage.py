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

from collections import namedtuple

from aquilon.config import Config


ShareInfo = namedtuple('ShareInfo', ['server', 'mount'])


# Utility functions for service / resource based disk mounts
# This should come from some external API...?
def cache_storage_data(only=None):
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
    found_header = False
    header_idx = {}
    with open(config.get("broker", "sharedata")) as datafile:
        for line in datafile:
            if line[0] == '#':
                # A header line
                found_header = True
                hdr = line[1:].rstrip().split('|')

                header_idx = {}
                for idx, name in enumerate(hdr):
                    header_idx[name] = idx

                # Silently discard lines that don't have all the required info
                for k in ["objtype", "pshare", "server", "dg"]:
                    if k not in header_idx:
                        found_header = False
            elif not found_header:
                # We haven't found the right header line
                continue
            else:
                fields = line.rstrip().split('|')
                if len(fields) != len(header_idx):  # Silently ignore invalid lines
                    continue
                if fields[header_idx["objtype"]] != "pshare":
                    continue

                sharedata[fields[header_idx["pshare"]]] = ShareInfo(
                    server=fields[header_idx["server"]],
                    mount="/vol/%s/%s" % (fields[header_idx["dg"]],
                                          fields[header_idx["pshare"]])
                )

                # Take a shortcut if we need just a single entry
                if only and only == fields[header_idx["pshare"]]:
                    break

        return sharedata


def find_storage_data(dbshare, cache=None):
    if not cache:
        cache = cache_storage_data(only=dbshare.name)
    if dbshare.name in cache:
        return cache[dbshare.name]
    else:
        return ShareInfo(server=None, mount=None)
