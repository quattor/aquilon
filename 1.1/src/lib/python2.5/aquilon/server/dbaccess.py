#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''If you can read this, you should be Documenting'''

import os
import exceptions

#from sqlalchemy import *
from sqlalchemy import Column, Integer, Sequence, String
from sqlalchemy.orm import mapper, relation, clear_mappers
from sasync.database import AccessBroker, transact
from twisted.internet import defer
from twisted.python import log

#from aquilon.aqdb.DB import meta, engine, Session
from aquilon.aqdb.location import *
from aquilon.aqdb.service import *


class DatabaseBroker(AccessBroker):
    """All database access eventually funnels through this class, to
    correctly handle backgrounding / threading within twisted.

    As a general rule, the methods here should reflect the actions
    being invoked by the client.
       
    """

    def startup(self):
        """This method normally creates Deferred objects for setting up
        the tables.  However, in our setup, all this work has already
        been done by importing aquilon.aqdb modules.
        
        """
        pass

    # FIXME: For now, the host methods are broken...
    #@transact
    #def addHost(self, name):
    #    #return self.host.insert().execute(name=name)
    #    newHost = Host(name)
    #    self.session.save(newHost)
    #    return [newHost]

    #@transact
    #def delHost(self, name):
    #    oldHost = self.session.query(Host).filter_by(name=name).one()
    #    self.session.delete(oldHost)
    #    return

    #@transact
    #def showHostAll(self):
    #    #return self.host.select().execute().fetchall()
    #    #log.msg(meta.__dict__)
    #    return self.session.query(AfsCell).all()

    #@transact
    #def showHost(self, name):
    #    #return self.session.query(Host).filter_by(name=name).one()
    #    return self.session.query(Host).filter_by(name=name).all()

    @transact
    def addLocation(self, **kwargs):
        #return self.host.insert().execute(name=name)
        newLocation = Location(**kwargs)
        self.session.save(newLocation)
        return [newLocation]

    @transact
    def delLocation(self, **kwargs):
        oldLocation = self.session.query(Location).filter_by(**kwargs).one()
        self.session.delete(oldLocation)
        return

    @transact
    def showLocation(self, **kwargs):
        if kwargs.has_key("type"):
            kwargs["type"] = self.session.query(LocationType).filter_by(
                    type=kwargs["type"]).one()
        return self.session.query(Location).filter_by(**kwargs).all()

    # This is a more generic solution... would be called with
    # transact_subs={"type":"LocationType"} as an argument alongside
    # type=whatever and/or name=whatever.
    #@transact
    #def showLocation(self, **kwargs):
    #    querycls = Location
    #    if kwargs.has_key("transact_subs"):
    #        subs = kwargs.pop("transact_subs")
    #        for (arg, cls) in subs.items():
    #            cls = globals().get(cls)
    #            if not issubclass(cls, aqdbBase):
    #                continue
    #            filter = {arg:kwargs[arg]}
    #            kwargs[arg] = self.session.query(cls).filter_by(**filter).one()
    #    return self.session.query(querycls).filter_by(**kwargs).all()

    @transact
    def showLocationType(self, **kwargs):
        return self.session.query(LocationType).filter_by(**kwargs).all()


# FIXME: This may no longer be needed... moved to aqdb.DB.
def sqlite():
    """Set up a default sqlite URI for use when none given."""
    osuser = os.environ.get('USER')
    dbdir = os.path.join( '/var/tmp', osuser, 'aquilondb' )
    try:
        os.makedirs( dbdir )
    except exceptions.OSError:
        pass
    return "sqlite:///" + os.path.join( dbdir, 'aquilon.db' )
