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
is properly backgrounded within twisted, and not blocking execution.

Most methods will be called as part of a callback chain, and should
expect to handle a generic result from whatever happened earlier in
the chain.

"""

import os
import re
import exceptions

from sasync.database import AccessBroker, transact
from sqlalchemy.exceptions import InvalidRequestError
from sqlalchemy import and_, or_
from twisted.internet import defer
from twisted.python import log
from twisted.python.failure import Failure

from aquilon import const
from aquilon.exceptions_ import RollbackException, NotFoundException, \
        AuthorizationException, ArgumentError, AquilonError, UnimplementedError
from aquilon.server import formats
from formats import printprep
from aquilon.aqdb.location import Location, LocationType, Company, Hub, \
        Continent, Country, City, Building, Rack, Chassis, Desk
from aquilon.aqdb.network import DnsDomain
from aquilon.aqdb.service import Service, ServiceInstance, \
        ServiceListItem, ServiceMap, HostList, HostListItem
from aquilon.aqdb.systems import System, Host, \
        QuattorServer, Domain, BuildItem
from aquilon.aqdb.configuration import Archetype, CfgPath, CfgTLD
from aquilon.aqdb.auth import UserPrincipal, Realm, Role
from aquilon.aqdb.hardware import Status, Vendor, MachineType, Model, \
        DiskType, Cpu, Machine, Disk, MachineSpecs
from aquilon.aqdb.interface import PhysicalInterface

# FIXME: This probably belongs in location.py
const.location_types = ("company", "hub", "continent", "country", "city",
        "building", "rack", "chassis", "desk")

class DatabaseBroker(AccessBroker):
    """All database access eventually funnels through this class, to
    correctly handle backgrounding / threading within twisted.

    As a general rule, the methods here should reflect the actions
    being invoked by the client.
    """
    def __init__(self, *url, **kwargs):
        AccessBroker.__init__(self, *url, **kwargs)
        self.safe_url = url and url[0] or ""
        m = re.match(r'^(oracle://.*?:)(.*)(@.*?)$', self.safe_url)
        if m:
            self.safe_url = m.group(1) + '********' + m.group(3)

    def startup(self):
        """This method normally creates Deferred objects for setting up
        the tables.  However, in our setup, all this work has already
        been done by importing aquilon.aqdb modules.
        """
        pass

    # expects to be run in a transact with a session...
    def _get_domain(self, domain):
        try:
            dbdomain = self.session.query(Domain).filter_by(name=domain).one()
        except InvalidRequestError, e:
            raise NotFoundException("Domain %s not found: %s"
                    % (domain, str(e)))
        return dbdomain

    # expects to be run in a transact with a session...
    def _get_status(self, status):
        try:
            dbstatus = self.session.query(Status).filter_by(name=status).one()
        except InvalidRequestError, e:
            raise ArgumentError("Status %s invalid (try one of %s): %s"
                    % (status, str(self.session.query(Status).all()), str(e)))
        return dbstatus

    # expects to be run in a transact with a session...
    def _get_machine(self, machine):
        try:
            dbmachine = self.session.query(Machine).filter_by(
                    name=machine).one()
        except InvalidRequestError, e:
            raise NotFoundException("Machine %s not found: %s"
                    % (machine, str(e)))
        return dbmachine

    # expects to be run in a transact with a session...
    def _get_service(self, service):
        try:
            dbservice = self.session.query(Service).filter_by(
                    name=service).one()
        except InvalidRequestError, e:
            raise NotFoundException("Service '%s' not found: %s" % (service, e))
        return dbservice

    @transact
    def verify_add_host(self, result, hostname, machine, domain, status,
            archetype, **kwargs):
        # To be able to enter this host into DSDB, there must be
        # - A valid machine being attached
        # - A bootable interface attached to the machine
        # - An IP Address attached to the interface
        # Assumes domain has been verified separately with verify_domain...
        dbdomain = self._get_domain(domain)
        dbstatus = self._get_status(status)
        dbmachine = self._get_machine(machine)
        dbarchetype = self._get_archetype(archetype)
        if not dbmachine.interfaces:
            raise ArgumentError("Machine '%s' has no interfaces." % machine)
        found_boot = False
        for interface in dbmachine.interfaces:
            if interface.boot:
                if found_boot:
                    # FIXME: Is this actually a problem?
                    raise ArgumentError("Multiple interfaces on machine '%s' are marked bootable" % machine)
                found_boot = True
        if not found_boot:
            raise ArgumentError("Machine '%s' requires a bootable interface." % machine)
        (short, dbdns_domain) = self._hostname_to_domain_and_string(hostname)
        if self.session.query(Host).filter_by(name=short,
                dns_domain=dbdns_domain).all():
            # The dsdb call would fail since the IP address is already in use...
            raise ArgumentError("Host '%s' already exists." % hostname)
        return printprep((short, dbdns_domain, dbmachine))

    @transact
    def add_host(self, result, hostname, machine, archetype, domain, status, **kwargs):
        # Assumes host has been added to dsdb.
        dbdomain = self._get_domain(domain)
        dbstatus = self._get_status(status)
        dbmachine = self._get_machine(machine)
        (short, dbdns_domain) = self._hostname_to_domain_and_string(hostname)
        host = Host(dbmachine, dbdomain, dbstatus, name=short,
                dns_domain=dbdns_domain, archetype=archetype)
        self.session.save(host)
        # Working around funky archetype handling in host creation...
        # Might not be necessary if/when Host uses the declarative mapper.
        self.session.flush()
        self.session.refresh(host)
        return printprep(host)

    @transact
    def verify_del_host(self, result, hostname, **kwargs):
        host = self._hostname_to_host(hostname)
        return printprep(host.machine)

    @transact
    def del_host(self, result, hostname, **kwargs):
        # Assumes host has been deleted from dsdb.
        host = self._hostname_to_host(hostname)
        # Hack to make sure the machine object is refreshed in future queries.
        dbmachine = host.machine
        for template in host.templates:
            log.msg("Before deleting host '%s', removing template '%s'"
                    % (host.fqdn, template.cfg_path))
            self.session.delete(template)
        self.session.delete(host)
        self.session.flush()
        self.session.refresh(dbmachine)
        return

    @transact
    def show_host_all(self, result, **kwargs):
        hosts = formats.HostList()
        hosts.extend(self.session.query(Host).all())
        return printprep(hosts)

    @transact
    def show_host(self, result, hostname, **kwargs):
        return printprep(self._hostname_to_host(hostname))

    @transact
    def show_hostiplist(self, result, archetype, **kwargs):
        hosts = formats.HostIPList()
        q = self.session.query(Host)
        if archetype:
            q = q.join('archetype').filter_by(name=archetype)
        hosts.extend(q.all())
        return printprep(hosts)

    @transact
    def verify_host(self, result, hostname, **kwargs):
        dbhost = self._hostname_to_host(hostname)
        return dbhost.fqdn

    @transact
    def add_location(self, result, name, type, parentname, parenttype,
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
        if fullname:
            optional_args["fullname"] = fullname
        if comments:
            optional_args["comments"] = comments

        newLocation = location_type(name=name, type_name=dblt,
                parent=parent, owner=user, **optional_args)
        return printprep([newLocation])

    @transact
    def del_location(self, result, name, type, user, **kwargs):
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
    def show_location(self, result, type=None, name=None, **kwargs):
        #log.msg("Attempting to generate a query...")
        query = self.session.query(Location)
        if type:
            # Not this easy...
            #kwargs["LocationType.type"] = type
            #log.msg("Attempting to add a type...")
            query = query.join('type').filter_by(type=type)
            query = query.reset_joinpoint()
        if name:
            try:
                #log.msg("Attempting query for one...")
                return printprep([query.filter_by(name=name).one()])
            except InvalidRequestError:
                raise NotFoundException(
                        "Location type='%s' name='%s' not found."
                        % (type, name))
        #log.msg("Attempting to query for all...")
        return printprep(query.all())

    @transact
    def show_location_type(self, result, user, **kwargs):
        return printprep(
                self.session.query(LocationType).filter_by(**kwargs).all())

    # Expects to be run under a transact with a session
    def _bind_required_services(self, dbhost):
        self.session.flush()
        self.session.refresh(dbhost)
        service_tld = self.session.query(CfgTLD).filter_by(type='service').one()
        for item in dbhost.archetype.service_list:
            service_bi = self.session.query(BuildItem).filter_by(
                    host=dbhost).join('cfg_path').filter_by(
                    tld=service_tld).filter(CfgPath.relative_path.like(
                    item.service.name + '/%')).first()
            if service_bi:
                continue
            dbinstance = self._choose_serviceinstance(dbhost, item.service)
            service_bi = BuildItem(dbhost, dbinstance.cfg_path, 3)
            dbhost.templates.append(service_bi)
            dbhost.templates._reorder()
            self.session.save(service_bi)
        self.session.flush()

    @transact
    def make_aquilon(self, result, build_info, hostname, os, **kwargs):
        """This takes the specified parameters and sets up the database
        relationships to create a quattor managed host.

        It does *not* create the pan template or compile the template -
        that logic is outside this method.
        """

        dbhost = self._hostname_to_host(hostname)
        # Currently, for the Host to be created it *must* be associated with
        # a Machine already.  If that ever changes, need to check here and
        # bail if dbhost.machine does not exist.

        # Need to get all the BuildItem objects for this host.
        # They should include:
        # - exactly one OS
        # - exactly one personality
        # And may include:
        # - many services
        # - many features

        try:
            os_cfgpath = self.session.query(CfgPath).filter_by(relative_path=os
                    ).join('tld').filter_by(type="os").one()
        except InvalidRequestError, e:
            raise NotFoundException(
                "OS '%s' config path information not found: %s"
                % (os, str(e)))
        os_bi = self.session.query(BuildItem).filter_by(host=dbhost).join(
                'cfg_path').filter_by(tld=os_cfgpath.tld).first()
        if os_bi:
            os_bi.cfg_path = os_cfgpath
        else:
            # FIXME: This could fail if there is already an item at 0
            os_bi = BuildItem(dbhost, os_cfgpath, 0)
        self.session.save_or_update(os_bi)

        try:
            personality = kwargs.get("personality", "ms/fid/spg/ice")
            personality_cfgpath = self.session.query(CfgPath).filter_by(
                    relative_path=personality).join('tld').filter_by(
                    type="personality").one()
        except InvalidRequestError, e:
            raise NotFoundException(
                "Personality '%s' config path information not found: %s"
                % (personality, str(e)))
        personality_bi = self.session.query(BuildItem).filter_by(
                host=dbhost).join('cfg_path').filter_by(
                tld=personality_cfgpath.tld).first()
        if personality_bi:
            personality_bi.cfg_path = personality_cfgpath
        else:
            # FIXME: This could fail if there is already an item at 1
            personality_bi = BuildItem(dbhost, personality_cfgpath, 1)
        self.session.save_or_update(personality_bi)

        self._bind_required_services(dbhost)

        self.session.flush()
        self.session.refresh(dbhost)
        build_info["dbhost"] = printprep(dbhost)
        # FIXME: Save this to the build table... maybe just carry around
        # the database object...
        build_info["buildid"] = -1
        return True

    @transact
    def verify_aquilon(self, result, build_info, hostname, **kwargs):
        dbhost = self._hostname_to_host(hostname)
        self.session.refresh(dbhost)

        found_os = False
        found_personality = False
        for t in dbhost.templates:
            if t.cfg_path.tld.type == 'os':
                found_os = True
            elif t.cfg_path.tld.type == 'personality':
                found_personality = True
            if found_os and found_personality:
                break
        if not found_os or not found_personality:
            raise ArgumentError("Please run `make aquilon --hostname %s` to give the host an os and personality." % hostname)

        self._bind_required_services(dbhost)

        build_info["dbhost"] = printprep(dbhost)
        # FIXME: Save this to the build table... maybe just carry around
        # the database object...
        build_info["buildid"] = -1
        return True

    @transact
    def cancel_make(self, failure, build_info):
        """Gets called as an Errback if the make_aquilon build fails."""
        error = failure.check(RollbackException)
        if not error:
            return failure
        # FIXME: Do the actual work of cancelling the make.
        return Failure(failure.value.cause)

    @transact
    def confirm_make(self, result, build_info):
        """Gets called if the make_aquilon build succeeds."""
        # FIXME: Should finalize the build table...

    # This should probably move over to UserPrincipal
    principal_re = re.compile(r'^(.*)@([^@]+)$')

    # This should be run under a @transact with a session
    def _get_or_create_UserPrincipal(self, user):
        if user is None:
            return user
        m = self.principal_re.match(user)
        if not m:
            raise ArgumentError("Could not parse user principal '%s'" % user)
        realm = m.group(2)
        user = m.group(1)
        dbrealm = self.session.query(Realm).filter_by(name=realm).first()
        if not dbrealm:
            dbrealm = Realm(name=realm)
            self.session.save(dbrealm)
            dbuser = UserPrincipal(user, realm=dbrealm)
            self.session.save(dbuser)
            return dbuser
        dbuser = self.session.query(UserPrincipal).filter_by(
                name=user.strip().lower(), realm=dbrealm).first()
        if not dbuser:
            dbuser = UserPrincipal(user, realm=dbrealm)
            self.session.save(dbuser)
            # Since we rely on the role being set by default, this forces
            # the role information to be loaded into the new object.
            self.session.flush()
        return dbuser

    @transact
    def get_user(self, result, user):
        return printprep(self._get_or_create_UserPrincipal(user))

    # Expects to be run under a transact with a session.
    def _get_or_create_quattorsrv(self, localhost):
        quattorsrv = self.session.query(QuattorServer).filter_by(
                name=localhost).first()
        if quattorsrv:
            return quattorsrv
        # FIXME: Assumes the QuattorServer is Aurora, and also that the
        # localhost is not defined as a System.
        quattorsrv = QuattorServer(name=localhost, dns_domain='ms.com',
                comments='Automatically generated entry')
        self.session.save(quattorsrv)
        return quattorsrv

    @transact
    def add_domain(self, result, domain, user, localhost, **kwargs):
        """Add the domain to the database, initialize as necessary."""
        dbuser = self._get_or_create_UserPrincipal(user)
        if not dbuser:
            raise AuthorizationException("Cannot create a domain without"
                    + " an authenticated connection.")
        quattorsrv = self._get_or_create_quattorsrv(localhost)
        # For now, succeed without error if the domain already exists.
        dbdomain = self.session.query(Domain).filter_by(name=domain).first()
        # FIXME: Check that the domain name is composed only of characters
        # that are valid for a directory name.
        if not dbdomain:
            dbdomain = Domain(domain, quattorsrv, dbuser)
            self.session.save_or_update(dbdomain)
        # We just need to confirm that the new domain can be added... do
        # not need anything from the DB to be passed to pbroker.
        return dbdomain.name

    @transact
    def del_domain(self, result, domain, user, **kwargs):
        """Remove the domain from the database."""
        # For now, succeed without error if the domain does not exist.
        try:
            dbdomain = self.session.query(Domain).filter_by(name=domain).one()
        except InvalidRequestError:
            return domain
        # Ignoring quattorsrv for now...
        # NOTE: Defaulting the name of the quattor server to quattorsrv.
        #quattorsrv = self.session.query(QuattorServer).filter_by(
        #        name='quattorsrv').one()
        #if quattorsrv != dbdomain.server:
        #    log.err("FIXME: Should be redirecting this operation.")
        if dbdomain:
            self.session.refresh(dbdomain)
            if dbdomain.hosts:
                raise ArgumentError("Cannot delete a domain with hosts still attached.")
            self.session.delete(dbdomain)
        # We just need to confirm that domain was removed from the db...
        # do not need anything from the DB to be passed to pbroker.
        return domain

    @transact
    def verify_domain(self, result, domain, localhost, **kwargs):
        """This checks both that the domain exists *and* that this is
        the correct server to handle requests for the domain."""
        quattorsrv = self._get_or_create_quattorsrv(localhost)
        try:
            dbdomain = self.session.query(Domain).filter_by(name=domain).one()
        except InvalidRequestError:
            raise NotFoundException("Domain '%s' not found." % domain)
        if quattorsrv != dbdomain.server:
            log.err("FIXME: Should be redirecting this operation.")
        return dbdomain.name

    @transact
    def show_domain_all(self, result, **kwargs):
        #stat.extend(self.session.query(Domain).all())
        return printprep(self.session.query(Domain).all())

    @transact
    def show_domain(self, result, domain, **kwargs):
        # FIXME: verify_domain(domain)
        return printprep(self.session.query(Domain).filter_by(name=domain).all())

    @transact
    def status(self, result, stat, user, **kwargs):
        """Return status information from the database."""
        #stat.extend(self.session.query(Domain).all())
        dbuser = self._get_or_create_UserPrincipal(user)
        if dbuser:
            stat.append("Connected as: %s [%s]" % (dbuser, dbuser.role.name))
        for line in stat:
            printprep(line)

    @transact
    def add_cpu(self, result, name, vendor, speed, **kwargs):
        v = self.session.query(Vendor).filter_by(name=vendor).first()
        if (v is None):
            raise ArgumentError("Vendor '"+vendor+"' not found!")

        c = Cpu (name=name, vendor=v, speed=speed)
        try:
            self.session.save(c)
        except InvalidRequestError, e:
            raise ValueError("Requested operation could not be completed!\n"+ e.__str__())

    @transact
    def add_disk(self, result, machine, type, capacity, **kwargs):
        m = self.session.query(Machine).filter_by(name=machine).first()
        if (m is None):
            raise ArgumentError('Unknown machine name')
        dt = self.session.query(DiskType).filter_by(type=type).one()
        if (dt is None):
            raise ArgumentError('Unknown disk type')

        d = Disk(machine=m,type=dt,capacity=capacity)
        try:
            self.session.save(d)
        except InvalidRequestError, e:
            raise ValueError("Requested operation could not be completed!\n"+ e.__str__())
        # Hack to make sure machine is accessible...
        printprep(d.machine)
        return d

    @transact
    def add_model(self, result, name, vendor, type, **kw):
        m = self.session.query(Model).filter_by(name=name).first()
        if (m is not None):
            raise ArgumentError('Specified model already exists')
        v = self.session.query(Vendor).filter_by(name = vendor).first()
        if (v is None):
            raise ArgumentError("Vendor '"+vendor+"' not found!")

        m = self.session.query(MachineType).filter_by(type=type).first()
        if (m is None):
            raise ArgumentError("Machine type '"+type+"' not found!")

        model = Model(name, v, m)
        self.session.save(model)

        if (kw.has_key('cputype') and kw['cputype'] is not None):
            ms = MachineSpecs(
                model=model,
                cpu=kw['cputype'],
                cpu_quantity=kw['cpunum'],
                memory=kw['mem'],
                disk_type=kw['disktype'],
                disk_capacity=kw['disksize'],
                nic_count=kw['nics']
            )
            self.session.save(ms)
        return "New model successfully created"

    @transact
    def show_model(self, result, **kwargs):
        q = self.session.query(Model)
        if (kwargs['name'] is not None):
            q = q.filter(Model.name.like(kwargs['name']+'%'))
        if (kwargs['vendor'] is not None):
            q = q.join('vendor').filter(Vendor.name.like(kwargs['vendor']+'%')).reset_joinpoint()
        if (kwargs['type'] is not None):
            q = q.join('machine_type').filter(MachineType.type.like(kwargs['type']+'%'))
        return printprep(q.all())

    # Expects to be run under a transact with a session.
    def _get_vendor(self, vendor):
        try:
            dbvendor = self.session.query(Vendor).filter_by(name=vendor).one()
        except InvalidRequestError, e:
            raise NotFoundException("Vendor '%s' not found: %s" % (vendor, e))
        return dbvendor

    # Expects to be run under a transact with a session.
    def _get_machine_type(self, type):
        try:
            dbtype = self.session.query(MachineType).filter_by(type=type).one()
        except InvalidRequestError, e:
            raise NotFoundException("Machine type '%s' not found: %s"
                    % (type, e))
        return dbtype

    @transact
    def del_model(self, result, name, vendor, type, **kwargs):
        dbvendor = self._get_vendor(vendor)
        dbmachine_type = self._get_machine_type(type)
        try:
            dbmodel = self.session.query(Model).filter_by(name=name,
                    vendor=dbvendor, machine_type=dbmachine_type).one()
        except InvalidRequestError, e:
            raise NotFoundException("Model '%s' with vendor %s and type %s not found: %s"
                    % (name, vendor, type, e))
        for ms in dbmodel.specifications:
            # FIXME: Log some details...
            log.msg("Before deleting model %s %s '%s', removing machine specifications." % (type, vendor, name))
            self.session.delete(ms)
        self.session.delete(dbmodel)
        return True

    # FIXME: This utility method may be better suited elsewhere.
    def force_int(self, label, value):
        if value is None:
            return None
        try:
            result = int(value)
        except Exception, e:
            raise ArgumentError("Expected an integer for %s: %s" % (label, e))
        return result

    @transact
    def add_machine(self, result, machine, model,
            cpuname, cpuvendor, cpuspeed, cpucount, memory, serial,
            **kwargs):
        dblocation = self._get_location(**kwargs)

        cpuspeed = self.force_int("cpuspeed", cpuspeed)
        cpucount = self.force_int("cpucount", cpucount)
        memory = self.force_int("memory", memory)

        dbmodel = self.session.query(Model).filter_by(name=model).first()
        if (dbmodel is None):
            raise ArgumentError("Model name '%s' not found!" % model);

        try:
            # If cpu.name format changes (currently name_speed), may need
            # to revisit this.
            cpu = self.session.query(Cpu).filter(
                    Cpu.name.like(cpuname.lower() + '%')).filter_by(
                    speed=cpuspeed).join('vendor').filter_by(
                    name=cpuvendor.lower()).one()
        except InvalidRequestError, e:
            raise NotFoundException("Could not find cpu with name like '%s%%', speed='%d', and vendor='%s': %s"
                    % (cpuname, cpuspeed, cpuvendor, e))

        try:
            # FIXME: These should have been optional.  Only override as needed.
            optional = {"cpu":cpu, "cpu_quantity":cpucount, "memory":memory}
            if serial:
                optional["serial_no"] = serial
            m = Machine(dblocation, dbmodel, name=machine, **optional)
            self.session.save(m)
        except InvalidRequestError, e:
            raise ValueError("Requested machine could not be created!\n"+e.__str__())
        return printprep(m)

    @transact
    def show_machine(self, result, **kwargs):
        try:
            q = self.session.query(Machine)
            if (kwargs['machine'] is not None):
                q = q.filter(Machine.name.like(kwargs['machine']+'%'))
            if (kwargs['location'] is not None and 
                kwargs['type'] is not None):
                if (kwargs['type'] not in ['chassis', 'rack', 'desk']):
                    raise ArgumentError ('Invalid location type')
                q = q.join('location').filter(Location.name.like(kwargs['location']+'%'))
                q = q.filter(LocationType.type == kwargs['type'])
                q = q.reset_joinpoint()
            if (kwargs['model'] is not None):
                q = q.join('model').filter(Model.name.like(kwargs['model']+'%'))
            return printprep(q.all())
        except InvalidRequestError, e:
            raise ValueError("Error while querying the database!\n"+e.__str__())

    @transact
    def verify_machine(self, result, machine, **kwargs):
        dbmachine = self._get_machine(machine)
        return printprep(dbmachine)

    @transact
    def del_machine(self, result, machine, **kwargs):
        try:
            m = self.session.query(Machine).filter_by(name=machine).one()
            for iface in m.interfaces:
                log.msg("Before deleting machine '%s', removing interface '%s' [%s] [%s] boot=%s)" % (m.name, iface.name, iface.mac, iface.ip, iface.boot))
                self.session.delete(iface)
            for disk in m.disks:
                log.msg("Before deleting machine '%s', removing disk '%s'" % (m.name, disk))
                self.session.delete(disk)
            self.session.delete(m)
        except InvalidRequestError, e:
            raise ValueError("Requested machine could not be deleted!\n"+e.__str__())
        return "Successfull deletion"

    @transact
    def add_interface(self, result, **kwargs):
        if (kwargs['interface'] is None):
            raise ArgumentError ('Interface name is not set!')
        if (kwargs['mac'] is None):
            raise ArgumentError('MAC address not set!')
        if (kwargs['machine'] is None):
            raise ArgumentError('Machine name isnot set!')
        ip_addr = (kwargs['ip'] is None) and '' or kwargs['ip']
        m = self.session.query(Machine).filter_by(name = kwargs['machine']).one()
        extra = {}
        if kwargs['interface'] == 'eth0':
            extra["boot"] = True
        i = PhysicalInterface(kwargs['interface'], kwargs['mac'], m, ip=ip_addr,
                **extra)
        self.session.save(i)
        # Hack to make sure machine is accessible...
        printprep(i.machine)
        return printprep(i)

    # Expects to run under a transact with a session.
    def _find_interface(self, interface, machine, mac, ip):
        q = self.session.query(PhysicalInterface)
        if interface:
            q = q.filter_by(name=interface)
        if machine:
            q = q.join('machine').filter_by(name=machine)
            q = q.reset_joinpoint()
        if mac:
            q = q.filter_by(mac=mac)
        if ip:
            q = q.filter_by(ip=ip)
        try:
            dbinterface = q.one()
        except InvalidRequestError, e:
            raise ArgumentError("Could not locate the interface, make sure it has been specified uniquely: " + str(e))
        return dbinterface

    @transact
    def del_interface(self, result, interface, machine, mac, ip, **kwargs):
        dbinterface = self._find_interface(interface, machine, mac, ip)
        dbmachine = dbinterface.machine
        if dbmachine.host and dbinterface.boot:
            raise ArgumentError("Cannot remove the bootable interface from a host.  Use `aq del host --hostname %s` first." % dbmachine.host.fqdn)
        self.session.delete(dbinterface)
        self.session.flush()
        self.session.refresh(dbmachine)
        return printprep(dbmachine)

    @transact
    def manage(self, result, domain, hostname, user, **kwargs):
        try:
            dbdomain = self.session.query(Domain).filter_by(name=domain).one()
        except InvalidRequestError:
            raise NotFoundException("Domain '%s' not found." % domain)
        dbhost = self._hostname_to_host(hostname)
        dbhost.domain = dbdomain
        self.session.save_or_update(dbhost)
        return

    # Expects to be run under a transact with a session.
    def _get_instance_parts(self, instance):
        dbdns_domain = None
        # A general solution would check all known dns domains for a match,
        # instead of assuming that the short name cannot contain dots.
        (short, dot, dns_domain) = instance.partition(".")
        if dns_domain:
            dbdns_domain = self.session.query(DnsDomain).filter_by(
                    name=dns_domain).first()
        if not dbdns_domain:
            # Hack for something like afs cell...
            if instance.endswith('.ms.com'):
                short = instance[:-7]
            else:
                short = instance
            dbdns_domain = self.session.query(DnsDomain).filter_by(
                    name='ms.com').one()
        return (short, dbdns_domain)

    @transact
    def add_service(self, result, service, instance, **kwargs):
        dbservice = self.session.query(Service).filter_by(name=service).first()
        if not dbservice:
            dbservice = Service(service)
            self.session.save(dbservice)
        if not instance:
            return printprep(dbservice)

        # FIXME: This will autocreate a service/instance CfgPath.  Does
        # there need to be a separate/explicit create of a
        # service/instance/client CfgPath?
        (short, dbdns_domain) = self._get_instance_parts(instance)
        dbsystem = self.session.query(System).filter_by(name=short,
                dns_domain=dbdns_domain).first()
        if not dbsystem:
            dbsystem = HostList(short, dns_domain=dbdns_domain)
            self.session.save(dbsystem)
        dbsi = ServiceInstance(dbservice, dbsystem)
        self.session.save(dbsi)
        self.session.flush()
        self.session.refresh(dbservice)
        return printprep(dbsi)

    @transact
    def show_service(self, result, service, **kwargs):
        q = self.session.query(Service)
        if not service:
            return printprep(q.all())
        try:
            dbservice = q.filter_by(name=service).one()
        except InvalidRequestError, e:
            raise NotFoundException("Service '%s' not found: %s" % (service, e))
        return printprep(dbservice)

    @transact
    def del_service(self, result, service, instance, **kwargs):
        # This should fail nicely if the service is required for an archetype.
        dbservice = self._get_service(service)
        if not instance:
            if dbservice.instances:
                raise ArgumentError("Cannot remove service with instances defined.")
            self.session.delete(dbservice)
            return "Success"
        (short, dbdns_domain) = self._get_instance_parts(instance)
        try:
            dbsystem = self.session.query(System).filter_by(name=short,
                    dns_domain=dbdns_domain).one()
        except InvalidRequestError, e:
            raise NotFoundException(
                    "Could not find a system matching instance %s: %s"
                    % (instance, e))
        dbsi = self.session.query(ServiceInstance).filter_by(
                system=dbsystem, service=dbservice).first()
        # FIXME: There may be dependencies...
        if dbsi:
            self.session.delete(dbsi)
        return "Success"

    # Expects to be run under a transact with a session
    def _get_archetype(self, archetype):
        try:
            dbarchetype = self.session.query(Archetype).filter_by(
                    name=archetype).one()
        except InvalidRequestError, e:
            raise NotFoundException("Archetype %s not found: %s"
                    % (archetype, e))
        return dbarchetype

    @transact
    def add_required_service(self, result, archetype, service, comments,
            **kwargs):
        dbarchetype = self._get_archetype(archetype)
        dbservice = self._get_service(service)
        try:
            dbsli = ServiceListItem(dbarchetype, dbservice, comments=comments)
            self.session.save_or_update(dbsli)
        except InvalidRequestError, e:
            # FIXME: Is there a better generic failure error?
            raise AquilonError("Could not add required service %s to %s: %s"
                    % (service, archetype, e))

    @transact
    def show_archetype(self, result, archetype, **kwargs):
        if archetype:
            return printprep(self._get_archetype(archetype))
        return printprep(self.session.query(Archetype).all())

    @transact
    def del_required_service(self, result, archetype, service, **kwargs):
        dbarchetype = self._get_archetype(archetype)
        dbservice = self._get_service(service)
        try:
            dbsli = self.session.query(ServiceListItem).filter_by(
                    service=dbservice, archetype=dbarchetype).one()
        except InvalidRequestError, e:
            raise NotFoundException("Could not find required service %s for %s: %s"
                    % (service, archetype, e))
        self.session.delete(dbsli)
        return True

    # Expects to be run under a transact with a session.
    def _get_host_builditem(self, dbhost, dbservice):
        for template in dbhost.templates:
            si = template.cfg_path.svc_inst
            if si and si.service == dbservice:
                return template
        return None

    # Expects to run under a transact with a session.
    # Modeled after least_loaded in aqdb/population_scripts.py
    def _choose_least_loaded(self, dbmaps):
        least_clients = None
        least_loaded = None
        for map in dbmaps:
            client_count = map.service_instance.counter
            if not least_loaded or client_count < least_clients:
                least_clients = client_count
                least_loaded = map.service_instance
        return least_loaded

    # Expects to run under a transact with a session.
    # Modeled after get_server_for in aqdb/population_scripts.py
    def _choose_serviceinstance(self, dbhost, dbservice):
        # FIXME: The database will support multiple algorithms...
        locations = [dbhost.location]
        while locations[-1].parent is not None:
            locations.append(locations[-1].parent)
        for location in locations:
            maps = self.session.query(ServiceMap).filter_by(
                    location=location).join('service_instance').filter_by(
                    service=dbservice).all()
            if len(maps) == 1:
                return maps[0].service_instance
            if len(maps) > 1:
                return self._choose_least_loaded(maps)
        raise ArgumentError("Could not find a relevant service map for service %s on host %s" %
                (dbservice.name, dbhost.fqdn))

    @transact
    def bind_client(self, result, hostname, service, instance, force, **kwargs):
        dbhost = self._hostname_to_host(hostname)
        dbservice = self._get_service(service)
        if instance:
            dbinstance = self._get_serviceinstance(dbservice, instance)
        else:
            dbinstance = self._choose_serviceinstance(dbhost, dbservice)
        dbtemplate = self._get_host_builditem(dbhost, dbservice)
        if dbtemplate:
            if dbtemplate.cfg_path == dbinstance.cfg_path:
                # Already set - no problems.
                return True
            if not force:
                raise ArgumentError("Host %s is already bound to %s, use unbind to clear first or rebind to force."
                        % (hostname, dbtemplate.cfg_path.relative_path))
            self.session.delete(dbtemplate)
        # FIXME: Should enforce that the instance has a server bound to it.
        positions = []
        self.session.flush()
        self.session.refresh(dbhost)
        for template in dbhost.templates:
            positions.append(template.position)
            if template.cfg_path == dbinstance:
                return printprep(dbhost)
        # Do not bind to 0 (os) or 1 (personality)
        i = 2
        while i in positions:
            i += 1
        bi = BuildItem(dbhost, dbinstance.cfg_path, i)
        self.session.save(bi)
        self.session.flush()
        self.session.refresh(dbhost)
        return printprep(dbhost)

    @transact
    def unbind_client(self, result, hostname, service, **kwargs):
        dbhost = self._hostname_to_host(hostname)
        dbservice = self._get_service(service)
        template = self._get_host_builditem(dbhost, dbservice)
        if template:
            self.session.delete(template)
            self.session.flush()
        self.session.refresh(dbhost)
        return printprep(dbhost)

    # Expects to be run under a transact with a session.
    def _get_serviceinstance(self, dbservice, instance):
        # FIXME: Quick hack for afs services... this needs to be reworked.
        if instance.endswith(".ms.com"):
            instance = instance[:-7]
        relative_path = "%s/%s" % (dbservice.name, instance)
        try:
            dbinstance = self.session.query(CfgPath).filter_by(
                    relative_path=relative_path,
                    tld=dbservice.cfg_path.tld).one()
        except InvalidRequestError, e:
            raise NotFoundException("Service %s instance %s not found (try aq add service to add it): %s"
                    % (dbservice.name, instance, e))
        if not dbinstance.svc_inst:
            raise NotFoundException("Service %s instance %s not found (try aq add service to add it)"
                    % (dbservice.name, instance))
        return dbinstance.svc_inst

    @transact
    def bind_server(self, result, hostname, service, instance, force, **kwargs):
        dbhost = self._hostname_to_host(hostname)
        dbservice = self._get_service(service)
        dbsi = self._get_serviceinstance(dbservice, instance)
        dbsystem = dbsi.system
        if not isinstance(dbsystem, HostList):
            raise ArgumentError("Cannot add a host to %s (System type: %s)"
                    % (dbsystem.fqdn, dbsystem.type))
        # FIXME: Does not check to see if the server is bound to some other
        # instance, so the force flag is never needed.
        self.session.refresh(dbsystem)
        positions = []
        for host in dbsystem.hosts:
            positions.append(host.position)
        position = 0
        while position in positions:
            position += 1
        hli = HostListItem(hostlist=dbsystem, host=dbhost, position=position)
        self.session.save(hli)
        self.session.flush()
        self.session.refresh(dbsystem)
        return True
        
    @transact
    def unbind_server(self, result, hostname, service, instance, **kwargs):
        dbhost = self._hostname_to_host(hostname)
        dbservice = self._get_service(service)
        dbsi = self._get_serviceinstance(dbservice, instance)
        dbsystem = dbsi.system
        if not isinstance(dbsystem, HostList):
            self.session.delete(dbsi)
            self.session.flush()
            self.session.refresh(dbservice)
            return True
        for item in dbsystem.hosts:
            if item.host == dbhost:
                self.session.delete(item)
        self.session.flush()
        self.session.refresh(dbsystem)
        return True

    # Expects to be run under a @transact method with session=True.
    def _get_location(self, **kwargs):
        location_type = None
        for lt in const.location_types:
            if kwargs.get(lt):
                if location_type:
                    raise ArgumentError("Single location can not be both %s and %s"
                            % (lt, location_type))
                location_type = lt
        if not location_type:
            return None
        try:
            dblocation = self.session.query(Location).filter_by(
                    name=kwargs[location_type]).join('type').filter_by(
                    type=location_type).one()
        except InvalidRequestError, e:
            raise NotFoundException("%s '%s' not found: %s"
                    % (location_type.capitalize(), kwargs[location_type], e))
        return dblocation

    @transact
    def map_service(self, result, service, instance, **kwargs):
        dbservice = self._get_service(service)
        dblocation = self._get_location(**kwargs)
        dbinstance = self._get_serviceinstance(dbservice, instance)
        dbmap = self.session.query(ServiceMap).filter_by(location=dblocation,
                service_instance=dbinstance).first()
        if not dbmap:
            dbmap = ServiceMap(dbinstance, dblocation)
            self.session.save(dbmap)
        self.session.flush()
        self.session.refresh(dbservice)
        self.session.refresh(dbinstance)
        return True

    @transact 
    def show_map(self, result, service, instance, **kwargs):
        dbservice = service and self._get_service(service) or None
        # FIXME: Instance is ignored for now.
        dblocation = self._get_location(**kwargs)
        # Nothing fancy for now - just show any relevant explicit bindings.
        q = self.session.query(ServiceMap)
        if dbservice:
            q = q.join('service_instance').filter_by(service=dbservice)
            q = q.reset_joinpoint()
        if dblocation:
            q = q.filter_by(location=dblocation)
        return printprep(q.all())

    @transact
    def unmap_service(self, result, service, instance, **kwargs):
        dbservice = self._get_service(service)
        dblocation = self._get_location(**kwargs)
        dbinstance = self._get_serviceinstance(dbservice, instance)
        dbmap = self.session.query(ServiceMap).filter_by(location=dblocation,
                service_instance=dbinstance).first()
        if dbmap:
            self.session.delete(dbmap)
        self.session.flush()
        self.session.refresh(dbservice)
        self.session.refresh(dbinstance)
        return True

    @transact
    def show_principal(self, result, principal, **kwargs):
        if not principal:
            return printprep(self.session.query(UserPrincipal).all())
        m = self.principal_re.match(principal)
        if not m:
            raise ArgumentError("Could not parse user principal '%s'"
                    % principal)
        realm = m.group(2)
        user = m.group(1)
        try:
            dbuser = self.session.query(UserPrincipal).filter_by(
                    name=user).join('realm').filter_by(name=realm).one()
        except InvalidRequestError, e:
            raise NotFoundException("Principal '%s' not found: %s"
                    % (principal, e))
        return printprep(dbuser)

    # Expects to be run under a @transact with a session.
    def _get_role(self, role):
        try:
            dbrole = self.session.query(Role).filter_by(name=role).one()
        except InvalidRequestError, e:
            raise ArgumentError("Role %s invalid (try one of %s): %s"
                    % (role, [str(role.name) for role in
                        self.session.query(Role).all()], str(e)))
        return dbrole

    @transact
    def permission(self, result, principal, role, createuser, createrealm,
            **kwargs):
        dbrole = self._get_role(role)
        m = self.principal_re.match(principal)
        if not m:
            raise ArgumentError("Could not parse user principal '%s'"
                    % principal)
        realm = m.group(2)
        user = m.group(1)
        dbrealm = self.session.query(Realm).filter_by(name=realm).first()
        if not dbrealm:
            if not createrealm:
                raise ArgumentError("Could not find realm '%s' to create principal '%s', use --createrealm to create a new record for the realm."
                        % (realm, principal))
            dbrealm = Realm(name=realm)
            self.session.save(dbrealm)
        dbuser = self.session.query(UserPrincipal).filter_by(name=user,
                realm=dbrealm).first()
        if not dbuser:
            if not createuser and not createrealm:
                raise ArgumentError("Could not find principal '%s' to permission, use --createuser to create a new record for the principal."
                        % principal)
            dbuser = UserPrincipal(user, realm=dbrealm)
            self.session.save(dbuser)
        # FIXME: Might want to force that at least one user retains aqd_admin
        # rights after this process.
        dbuser.role = dbrole
        self.session.save_or_update(dbuser)
        return True

    @transact
    def regenerate_machines(self, result, **kwargs):
        return printprep(self.session.query(Machine).all())

    @transact
    def regenerate_hosts(self, result, **kwargs):
        return printprep(self.session.query(Host).all())

    # Expects to be run under a @transact method with session=True.
    def _hostname_to_domain_and_string(self, hostname):
        if not hostname:
            raise ArgumentError("No hostname specified.")
        (short, dot, dns_domain) = hostname.partition(".")
        if not dns_domain:
            raise ArgumentError(
                    "'%s' invalid, hostname must be fully qualified."
                    % hostname)
        if not short:
            raise ArgumentError( "'%s' invalid, missing host name." % hostname)
        try:
            dbdns_domain = self.session.query(DnsDomain).filter_by(
                    name=dns_domain).one()
        except InvalidRequestError, e:
            raise NotFoundException("DNS domain '%s' for '%s' not found: %s"
                    % (dns_domain, hostname, e))
        return (short, dbdns_domain)

    # Expects to be run under a @transact method with session=True.
    def _hostname_to_host(self, hostname):
        (short, dbdns_domain) = self._hostname_to_domain_and_string(hostname)
        try:
            host = self.session.query(Host).filter_by(
                    name=short, dns_domain=dbdns_domain).one()
        except InvalidRequestError, e:
            raise NotFoundException("Host '%s' not found." % hostname)
        return host

