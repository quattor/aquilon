""" Manufacturer names """
import os

from aquilon.aqdb.table_types.name_table import make_name_class

Vendor = make_name_class('Vendor', 'vendor')
vendor = Vendor.__table__

table = vendor

def populate(db, *args, **kw):
    sess = db.Session()
    if len(sess.query(Vendor).all()) < 1:
        import aquilon.aqdb.cfg.cfg_path as cfg
        created = []
        cfg_base = db.config.get("broker", "kingdir")
        assert os.path.isdir(cfg_base)

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
                        sess.add(a)
                    except Exception,e:
                        sess.rollback()
                        sys.stderr.write(e)
                        continue
                    created.append(j)

        aurora_vendor = Vendor(name='aurora_vendor',
                            comments='Placeholder vendor for Aurora hardware.')

        sess.save(aurora_vendor)
        created.append(aurora_vendor)

        for v in ['bnt', 'cisco']:
            if not v in created:
                dbv = Vendor(name=v)
                try:
                    sess.save(dbv)
                except Exception, e:
                    sess.rollback()
                    print >> sys.stderr, e
                    continue
                created.append(v)

        try:
            sess.commit()
        except Exception,e:
            print >> sys.stderr, e
        finally:
            sess.close()
        print 'created %s vendors'%(len(created))



# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
