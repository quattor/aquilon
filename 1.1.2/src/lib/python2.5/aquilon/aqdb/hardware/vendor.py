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
sys.path.insert(0,'..')
sys.path.insert(1,'../..')
sys.path.insert(2,'../../..')

from name_table import *

Vendor = make_name_class('Vendor','vendor')
vendor = Vendor.__table__

def populate_vendor():
    from db_factory import db_factory
    from db import empty
    
    dbf = db_factory()
    s = dbf.session()

    if empty(vendor):
        print "Populating vendor"
        import configuration as cfg
        from aquilon import const
        d=os.path.join(str(const.cfg_base),'hardware')
        created=[]
        for i in os.listdir(d):
            if i == 'ram':
                continue
            for j in os.listdir(os.path.join(d,i)):
                if j in created:
                    continue
                else:
                    a=Vendor(name=j)
                    try:
                        s.save(a)
                    except Exception,e:
                        s.rollback()
                        print >> sys.stderr, e
                        continue
                    created.append(j)
        #hack alert:
        b=Vendor(name = 'hp')
        s.save(b)
        b = Vendor(name='verari')
        s.save(b)
        try:
            s.commit()
        except Exception,e:
            print >> sys.stderr, e
        finally:
            s.close()
