#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" The high level configuration elements in use """
from datetime import datetime

import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(DIR, '..'))

from table_types.subtype import subtype

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

def populate():
    from db_factory import db_factory, Base
    dbf = db_factory()

    cfg_base = dbf.config.get("broker", "kingdir")
    assert(cfg_base)

    Base.metadata.bind = dbf.engine
    Base.metadata.bind.echo = True
    s = dbf.session()

    tld.create(checkfirst = True)

    if len(s.query(Tld).all()) < 1:
        import os
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
            s.add(t)
        s.commit()

        a=s.query(Tld).first()
        assert(a)
