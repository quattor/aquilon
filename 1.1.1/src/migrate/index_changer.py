#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" intended to make the new tables during migration """

from depends import *

import db_factory
dbf = db_factory.db_factory()

Base.metadata.bind = dbf.engine

if __name__ == '__main__':
    print dbf.dsn

    m = Base.metadata
    m.reflect()
    for t in m.table_iterator():
        t = Table(t.name, m)
        print '%s:%s\n'%(t.name,t.constraints)
    ipshell()
