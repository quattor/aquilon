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
import re
import exceptions

from sasync.database import AccessBroker, transact
from sqlalchemy.exceptions import InvalidRequestError
from twisted.internet import defer
from twisted.python import log

from aquilon import const
from aquilon.exceptions_ import RollbackException
from aquilon.server.exceptions_ import NotFoundException, AuthorizationException
from aquilon.aqdb.location import *
from aquilon.aqdb.service import *
from aquilon.aqdb.configuration import *
from aquilon.aqdb.auth import *
from aquilon.aqdb.hardware import *

# FIXME: This probably belongs in location.py
const.location_types = ("company", "hub", "continent", "country", "city",
        "building", "rack", "chassis", "desk")

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
    def add_location(self, name, type, parentname, parenttype,
            fullname, comments, user, **kwargs):
        newLocation = self.session.query(Location).filter_by(name=name
                ).join('type').filter_by(type=type).first()
        if newLocation:
            # FIXME: Technically this is coming in with an http PUT,
            # which should try to adjust state and succeed if everything
            # is alright.
            raise ArgumentError("Location name=%s type=%s already exists."
                    % (name, type))
        try:
            parent = self.session.query(Location).filter_by(name=parentname
                    ).join('type').filter_by(type=parenttype).one()
        except InvalidRequestError:
            raise ArgumentError(
                    "Parent Location type='%s' name='%s' not found."
                    % (parenttype, parentname))
        # Incoming looks like 'city', need the City class.
        location_type = globals()[type.capitalize()]
        if not issubclass(location_type, Location):
            raise ArgumentError("%s is not a known location type" % type)
        try:
            dblt = self.session.query(LocationType).filter_by(type=type).one()
        except InvalidRequestError:
            raise ArgumentError("Invalid type '%s'" % type)

        # Figure out if it is valid to add this type of child to the parent...
        found_parent = False
        found_new = False
        for t in const.location_types:
            if t == parenttype:
                # Great, found the parent type in the list before requested type
                found_parent = True
                continue
            if t != type:
                # This item is neither parent nor new, keep going...
                continue
            # Moment of truth.
            if found_parent:
                # We saw the parent earlier - life is good.
                found_new = True
                break
            raise ArgumentError("type %s cannot be a parent of %s",
                    (parenttype, type))
        if not found_new:
            raise ArgumentError("unknown type %s", type)

        optional_args = {}
        optional_args["fullname"] = fullname
        if comments:
            optional_args["comments"] = comments

        newLocation = location_type(name=name, type_name=dblt,
                parent=parent, owner=user, **optional_args)
        return [newLocation]

    @transact
    def del_location(self, name, type, user, **kwargs):
        try:
            oldLocation = self.session.query(Location).filter_by(name=name
                    ).join('type').filter_by(type=type).one()
        except InvalidRequestError:
            raise NotFoundException(
                    "Location type='%s' name='%s' not found."
                    % (type, name))
        self.session.delete(oldLocation)
        return

    @transact
    def show_location(self, type=None, name=None, **kwargs):
        log.msg("Attempting to generate a query...")
        query = self.session.query(Location)
        if type:
            # Not this easy...
            #kwargs["LocationType.type"] = type
            log.msg("Attempting to add a type...")
            query = query.join('type').filter_by(type=type)
            query = query.reset_joinpoint()
        if name:
            try:
                log.msg("Attempting query for one...")
                return [query.filter_by(name=name).one()]
            except InvalidRequestError:
                raise NotFoundException(
                        "Location type='%s' name='%s' not found."
                        % (type, name))
        log.msg("Attempting to query for all...")
        return query.all()

    @transact
    def show_location_type(self, **kwargs):
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

    # This should probably move over to UserPrincipal
    principal_re = re.compile(r'^(.*)@([^@]+)$')
    def split_principal(self, user):
        if not user:
            return (user, None)
        m = self.principal_re.match(user)
        if m:
            return (m.group(1), m.group(2))
        return (user, None)

    @transact
    def add_domain(self, domain, user, **kwargs):
        """Add the domain to the database, initialize as necessary."""
        (user, realm) = self.split_principal(user)
        # FIXME: UserPrincipal should include the realm...
        dbuser = self.session.query(UserPrincipal).filter_by(name=user).first()
        if not dbuser:
            if not user:
                raise AuthorizationException("Cannot create a domain without"
                        + " an authenticated connection.")
            dbuser = UserPrincipal(user)
            self.session.save_or_update(dbuser)
        # NOTE: Defaulting the name of the quattor server to quattorsrv.
        quattorsrv = self.session.query(QuattorServer).filter_by(
                name='quattorsrv').one()
        # NOTE: Does DNS domain matter here?
        dnsdomain = self.session.query(DnsDomain).filter_by(
                name='one-nyp').one()
        # For now, succeed without error if the domain already exists.
        dbdomain = self.session.query(Domain).filter_by(name=domain).first()
        # FIXME: Check that the domain name is composed only of characters
        # that are valid for a directory name.
        if not dbdomain:
            dbdomain = Domain(domain, quattorsrv, dnsdomain, dbuser)
            self.session.save_or_update(dbdomain)
        # We just need to confirm that the new domain can be added... do
        # not need anything from the DB to be passed to pbroker.
        return dbdomain.name

    @transact
    def del_domain(self, domain, user, **kwargs):
        """Remove the domain from the database."""
        # Do we need to delete any dependencies before deleting the domain?
        (user, realm) = self.split_principal(user)
        # NOTE: Defaulting the name of the quattor server to quattorsrv.
        quattorsrv = self.session.query(QuattorServer).filter_by(
                name='quattorsrv').one()
        # For now, succeed without error if the domain does not exist.
        try:
            dbdomain = self.session.query(Domain).filter_by(name=domain).one()
        except InvalidRequestError:
            return domain
        if quattorsrv != dbdomain.server:
            log.err("FIXME: Should be redirecting this operation.")
        # FIXME: Entitlements will need to happen at this point.
        if dbdomain:
            self.session.delete(dbdomain)
        # We just need to confirm that domain was removed from the db...
        # do not need anything from the DB to be passed to pbroker.
        return domain

    @transact
    def verify_domain(self, domain):
        """This checks both that the domain exists *and* that this is
        the correct server to handle requests for the domain."""
        # NOTE: Defaulting the name of the quattor server to quattorsrv.
        quattorsrv = self.session.query(QuattorServer).filter_by(
                name='quattorsrv').one()
        try:
            dbdomain = self.session.query(Domain).filter_by(name=domain).one()
        except InvalidRequestError:
            raise NotFoundException("Domain '%s' not found." % domain)
        if quattorsrv != dbdomain.server:
            log.err("FIXME: Should be redirecting this operation.")
        return dbdomain.name

    @transact
    def status(self, stat, user, **kwargs):
        """Return status information from the database."""
        stat.extend(self.session.query(Domain).all())
        (user, realm) = self.split_principal(user)
        # FIXME: UserPrincipal should include the realm...
        dbuser = self.session.query(UserPrincipal).filter_by(name=user).first()
        if user and not dbuser:
            dbuser = UserPrincipal(user)
            self.session.save_or_update(dbuser)
        if dbuser:
            stat.append(dbuser)

    @transact
    def add_model (self, name, vendor, hardware, machine, **kwargs):
        v,h,m = None
        try:
            v = self.session.query(Vendor).filter_by(name = vendor).one()
        except StandardError, e:
            raise ValueError("Vendor '"+vendor+"' not found!")

        try:
            h = self.session.query(HardwareType).filter_by(type = hardware).one()
        except StandardError, e:
            raise ValueError("Hardware type '"+hardware+"' not found!")

        try:
            m = self.session.query(MachineType).filter_by(type = machine).one()
        except StandardError, e:
            raise ValueError("Machine type '"+machine+"' not found!")

#        try:
#            model = Model(name, v, h, m)
#            self.session.save(Model)
#        except StandardError, e:
#            raise ValueError("Vendor '"+vendor+"' not found!")
        return "New model successfully created"
