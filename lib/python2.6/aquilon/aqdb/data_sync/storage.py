# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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
