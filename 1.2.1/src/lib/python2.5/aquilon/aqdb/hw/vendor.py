#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Status is an overloaded term, but we use it to represent various stages of
    deployment, such as production, QA, dev, etc. each of which are also
    overloaded terms... """


import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from aquilon.aqdb.table_types.name_table import make_name_class


Vendor = make_name_class('Vendor','vendor')
vendor = Vendor.__table__


def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    vendor.create(checkfirst = True)

    if len(s.query(Vendor).all()) < 1:
        import aquilon.aqdb.cfg.cfg_path as cfg
        cfg_base = dbf.config.get("broker", "kingdir")
        assert(cfg_base)

        #in case user's config doesn't have one...
        if not cfg_base.endswith('/'):
            cfg_base += '/'
        cfg_base += 'hardware'

        created=[]
        for i in os.listdir(cfg_base):
            if i == 'ram':
                continue
            for j in os.listdir(os.path.join(cfg_base,i)):
                if j in created:
                    continue
                else:
                    a=Vendor(name=j)
                    try:
                        s.save(a)
                    except Exception,e:
                        s.rollback()
                        sys.stderr.write(e)
                        continue
                    created.append(j)

        try:
            s.commit()
        except Exception,e:
            print >> sys.stderr, e
        finally:
            s.close()

    print 'created %s vendors'%(len(created))
    if Base.metadata.bind.echo == True:
        Base.metadata.bind.echo == False
