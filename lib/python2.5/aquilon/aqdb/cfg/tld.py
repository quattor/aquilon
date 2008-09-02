#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" The high level configuration elements in use """

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from aquilon.aqdb.table_types.subtype import subtype


tl_doc = """ Configuration Top Level Directory or 'cfg_tld' are the high level
            namespace categories and live as the directories in template-king:

            aquilon   (the only archetype for now)
            os        (major types (linux,solaris) prefabricated)
            hardware  (vendors + types prefabricated)
            services
            feature
            personality """

Tld= subtype('Tld', 'tld', tl_doc)
tld = Tld.__table__
tld.primary_key.name = 'tld_pk'

table = tld

def populate(db, *args, **kw):
    if len(db.s.query(Tld).all()) > 0:
        return

    cfg_base = db.config.get("broker", "kingdir")
    assert(cfg_base)

    tlds=[]
    for i in os.listdir(cfg_base):
        p = os.path.abspath(os.path.join(cfg_base, i))
        if os.path.isdir(p):
            # Hack to consider all subdirectories of the archetype
            # as a tld.
            if i == "aquilon":
                for j in os.listdir(p):
                    if os.path.isdir(os.path.abspath(os.path.join(p, j))):
                        tlds.append(j)
            elif i == ".git":
                continue
            else:
                tlds.append(i)

    print "Adding these TLDs: ", str(tlds)
    for i in tlds:
        t =Tld(type=i)
        db.s.add(t)
    db.s.commit()

    a=db.s.query(Tld).first()
    assert(a)

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon

