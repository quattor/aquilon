#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" Hub is a subclass of Location """

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.loc.location import Location, location


class Hub(Location):
    """ Hub is a subtype of location """
    __tablename__ = 'hub'
    __mapper_args__ = {'polymorphic_identity' : 'hub'}
    id = Column(Integer,
                ForeignKey('location.id', name = 'hub_loc_fk',
                           ondelete = 'CASCADE'),
                primary_key=True)

hub = Hub.__table__
hub.primary_key.name = 'hub_pk'

table = hub

def populate(db, *args, **kw):

    s = db.session()

    hub.create(checkfirst = True)

    _hubs = {
        'hk':'Non-japan Asia',
        'ln' : 'Europe',
        'ny' : 'Americas',
        'tk' : 'Japan'
        }

    if len(s.query(Hub).all()) < len(_hubs.keys()):
        for h in _hubs:
            a = Hub(name=h, fullname = _hubs[h], parent_id = 1) #FIX ME
            s.add(a)
        s.commit()


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-


