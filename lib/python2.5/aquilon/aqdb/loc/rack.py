""" Rack is a subclass of Location """

from sqlalchemy import Column, Integer, Numeric, ForeignKey

from aquilon.aqdb.loc.location import Location, location
from aquilon.aqdb.column_types.aqstr import AqStr

class Rack(Location):
    """ Rack is a subtype of location """
    __tablename__ = 'rack'
    __mapper_args__ = {'polymorphic_identity' : 'rack'}
    id = Column(Integer,
                ForeignKey('location.id', name = 'rack_loc_fk',
                           ondelete = 'CASCADE'), primary_key=True)

    #TODO: POSTHASTE: constrain to alphabetic in row, and make both non-nullable
    rack_row    = Column(AqStr(4), nullable = True)
    rack_column = Column(Integer,  nullable = True)

rack = Rack.__table__
rack.primary_key.name = 'rack_pk'
table = rack

def populate(sess, *args, **kw):

    if len(sess.query(Rack).all()) < 1:
        from aquilon.aqdb.loc.building import Building

        bldg = {}

        try:
            np = sess.query(Building).filter_by(name='np').one()
        except Exception, e:
            print e
            sys.exit(9)

        rack_name = 'np3'
        a = Rack(name = rack_name, fullname = 'Rack %s'%(rack_name),
                     parent = np, comments = 'AutoPopulated')
        sess.add(a)
        try:
            sess.commit()
        except Exception, e:
            print e


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
