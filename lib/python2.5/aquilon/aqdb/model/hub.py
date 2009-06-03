""" Hub is a group of continents.
    Got that straight? A GROUP OF CONTINENTS.

    We are declaring what hubs are for Aquilon.
    It's no good arguing along the lines of "but, I think it means X,
    therefore your implementation isn't right". It doesn't mean X.
    We'll ensure that all meanings are described as much as possible.
    That's not complete yet. It doesn't change the fact that in Aquilon,
    it doesn't mean X.

    Move along.

    Nothing to see here.

    Really."""

from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.model import Location

class Hub(Location):
    """ Hub is a subtype of location """
    __tablename__ = 'hub'
    __mapper_args__ = {'polymorphic_identity':'hub'}
    id = Column(Integer, ForeignKey('location.id',
                                    name='hub_loc_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

hub = Hub.__table__
hub.primary_key.name='hub_pk'

table = hub

def populate(sess, *args, **kw):

    _hubs = {
        'hk':'Asia',
        'ln':'Europe',
        'ny':'Americas',
    }

    if len(sess.query(Hub).all()) < len(_hubs.keys()):
        for h in _hubs:
            #FIX ME: don't fix it on id = 1 (breaks in certain conditions)
            a = Hub(name=h, fullname=_hubs[h], parent_id=1)
            sess.add(a)
        sess.commit()


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
