#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""All database access should funnel through this module to ensure that it
is properly backgrounded within twisted, and not blocking execution."""

import os
import exceptions

from sasync.database import AccessBroker, transact
from twisted.internet import defer
from twisted.python import log

from aquilon.exceptions_ import RollbackException
from aquilon.aqdb.location import *
from aquilon.aqdb.service import *
from aquilon.aqdb.configuration import *


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
        query = self.session.query(Location)
        if kwargs.has_key("type"):
            # Not this easy...
            #kwargs["LocationType.type"] = kwargs.pop("type")
            query = query.join('type').filter_by(type=kwargs.pop("type"))
            query = query.reset_joinpoint()
        if kwargs:
            query = query.filter_by(**kwargs)
        return query.all()

    # This is a more generic solution... would be called with
    # transact_subs={"type":"LocationType"} as an argument alongside
    # type=whatever and/or name=whatever.
    # It would then be much more general than just Location.
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

    @transact
    def make_aquilon(self, **kwargs):
        """This creates a template file and saves a copy in the DB.
        
        It does *not* do pan compile... that happens outside this method.
        """

        fqdn = "aquilon00.one-nyp.ms.com"
        #archetype = self.session.query(Archetype).filter(
        #        Archetype.name=="aquilon").one()
        #base_template = "%s/base" % archetype.name
        #final_template = "%s/final" % archetype.name
        base_template = "archetype/aquilon/base"
        final_template = "archetype/aquilon/final"
        os_template = "os/linux/4.0.1-x86_64/config"
        personality_template = "usage/grid/config"
        hardware = "machine/na/np/6/31_c1n3"
        interfaces = [ {"ip":"172.31.29.82", "netmask":"255.255.255.128",
                "broadcast":"172.31.29.127", "gateway":"172.31.29.1",
                "bootproto":"dhcp", "name":"eth0"} ]
        services = [ "service/afs/q.ny.ms.com/client/config" ]

        templates = []
        templates.append(base_template)
        templates.append(os_template)
        for service in services:
            templates.append(service)
        templates.append(personality_template)
        templates.append(final_template)

        template_lines = []
        template_lines.append("object template %(fqdn)s;\n")
        template_lines.append("""include { "pan/units" };\n""")
        template_lines.append(""""/hardware" = create("%s");\n""" % hardware)
        for interface in interfaces:
            template_lines.append(""""/system/network/interfaces/%(name)s" = nlist("ip", "%(ip)s", "netmask", "%(netmask)s", "broadcast", "%(broadcast)s", "gateway", "%(gateway)s", "bootproto", "%(bootproto)s");""")
        for template in templates:
            template_lines.append("""include { "%s" };""" % template)
        template_string = "\n".join(template_lines)

        # FIXME: Save this to the build table...
        buildid = 0
        return fqdn, buildid, template_string

    @transact
    def cancel_make(self, failure):
        """Gets called if the make_aquilon build fails."""
        failure.trap(RollbackException)
        # FIXME: re-raising the original error might rollback the
        # transaction - may need a different way to do this.
        # One hack would be to just return the error, and have an
        # addBoth() that checked to see if it was passed an exception,
        # and then raise it.
        raise failure.value.cause

    @transact
    def confirm_make(self, buildid):
        """Gets called if the make_aquilon build succeeds."""
        # FIXME: Should finalize the build table...

