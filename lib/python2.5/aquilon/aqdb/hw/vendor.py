#!/ms/dist/python/PROJ/core/2.5.0/bin/python

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

Vendor = make_name_class('Vendor', 'vendor')
vendor = Vendor.__table__

table = vendor

def populate(db, *args, **kw):

    if len(db.s.query(Vendor).all()) < 1:
        import aquilon.aqdb.cfg.cfg_path as cfg
        created = []
        cfg_base = db.config.get("broker", "kingdir")
        assert(cfg_base)

        #in case user's config doesn't have one...
        if not cfg_base.endswith('/'):
            cfg_base += '/'
        cfg_base += 'hardware'

        for i in os.listdir(cfg_base):
            if i == 'ram':
                continue
            for j in os.listdir(os.path.join(cfg_base,i)):
                if j in created:
                    continue
                else:
                    a=Vendor(name=j)
                    try:
                        db.s.save(a)
                    except Exception,e:
                        db.s.rollback()
                        sys.stderr.write(e)
                        continue
                    created.append(j)

        aurora_vendor = Vendor(name='aurora_vendor',
                            comments='Placeholder vendor for Aurora hardware.')

        db.s.save(aurora_vendor)
        created.append(aurora_vendor)

        for v in ['bnt', 'cisco']:
            if not v in created:
                dbv = Vendor(name=v)
                try:
                    db.s.save(dbv)
                except Exception, e:
                    db.s.rollback()
                    print >> sys.stderr, e
                    continue
                created.append(v)

        try:
            db.s.commit()
        except Exception,e:
            print >> sys.stderr, e
        finally:
            db.s.close()
        print 'created %s vendors'%(len(created))



# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

