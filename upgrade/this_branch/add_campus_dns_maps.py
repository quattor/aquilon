#! /usr/bin/env python2.6
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
