#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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
Add default DNS domain maps for existing campuses
"""

import os
import sys

BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(os.path.join(BINDIR, "..", "..", "lib", "python2.6"))

import aquilon.aqdb.depends
from aquilon.config import Config

from aquilon.aqdb.model import Base, Campus, DnsDomain, DnsMap
from aquilon.aqdb.db_factory import DbFactory

db = DbFactory()
Base.metadata.bind = db.engine

session = db.Session()

def main():
    q = session.query(Campus)
    for campus in q.all():
        print "Processing {0:l}".format(campus)

        name = campus.fullname.lower().strip().replace(" ", "-") + ".ms.com"
        dbdns_domain = DnsDomain.get_unique(session, name)
        if not dbdns_domain:
            print "    - DNS Domain %s does not exist, skipping" % name
            continue

        map = DnsMap.get_unique(session, location=campus,
                                dns_domain=dbdns_domain)
        if map:
            print "    - {0} is already mapped, skipping".format(dbdns_domain)
            continue

        campus.dns_maps.append(DnsMap(dns_domain=dbdns_domain))
        print "    * Mapping {0:l} to {1:l}".format(dbdns_domain, campus)

    session.commit()

if __name__ == '__main__':
    main()
