#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon

import os
import socket

from twisted.internet import defer
from twisted.internet import reactor
from twisted.python import log

from aquilon.server.processes import ProcessBroker
from aquilon.server.templates import TemplateCreator
from aquilon.exceptions_ import AquilonError

#=============================================================================#

class BrokerError(StandardError):
    def __init__ (self):
        self.errorList = []

    def errorMessage (self):
        return "\n".join(self.errorList)

    def pushError (self, errorMessage):
        self.errorList.append(errorMessage)

#=============================================================================#

def raise_exception(msg):
    raise AquilonError(msg)

#=============================================================================#

class Broker(object):
    def __init__(self, dbbroker, azbroker):
        self.dbbroker = dbbroker
        self.azbroker = azbroker
        self.pbroker = ProcessBroker()
        self.template_creator = TemplateCreator()
        self.osuser = os.environ.get('USER')
        self.localhost = socket.gethostname()
        if self.osuser == 'cdb' and os.path.exists('/var/quattor'):
            self.basedir = "/var/quattor"
            self.git_templates_url = "http://%s/templates" % self.localhost
        else:
            self.basedir = "/var/tmp/%s/quattor" % self.osuser
            self.git_templates_url = "http://%s:6901/templates" % self.localhost
        self.profilesdir = os.path.join(self.basedir,
                "web", "htdocs", "profiles")
        self.depsdir = os.path.join(self.basedir, "deps")
        self.hostsdir = os.path.join(self.basedir, "hosts")
        self.templatesdir = os.path.join(self.basedir, "templates")
        self.plenarydir = os.path.join(self.basedir, "plenary")
        self.kingdir = os.path.join(self.basedir, "template-king")
        self.repdir = os.path.join(self.basedir, "swrep")
        self.rundir = os.path.join(self.basedir, "run")
        self.default_domain = ".ms.com"
        self.git_path = "/ms/dist/fsf/PROJ/git/1.5.4.2/bin"
        self.git = os.path.join(self.git_path, "git")
        self.htpasswd = "/ms/dist/elfms/PROJ/apache/2.2.6/bin/htpasswd"
        self.domain_name = "production"
        self.dsdb = "/ms/dist/aurora/PROJ/dsdb/4.4.2/bin/dsdb"

        for d in [self.basedir, self.profilesdir, self.depsdir, self.hostsdir,
                self.plenarydir, self.rundir]:
            if os.path.exists(d):
                continue
            try:
                os.makedirs(d)
            except OSError, e:
                log.err(e)

# --------------------------------------------------------------------------- #

    def show_location(self, arguments, request_path, user):
        # just a facade method
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "show", request_path)
        d = d.addCallback(self.dbbroker.show_location, session=True,
                user=user, **arguments)
        return d

# --------------------------------------------------------------------------- #

    def show_location_type(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "show", request_path)
        d = d.addCallback(self.dbbroker.show_location_type, session=True,
                user=user, **arguments)
        return d

# --------------------------------------------------------------------------- #

    def add_location(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "add", request_path)
        d = d.addCallback(self.dbbroker.add_location, session=True,
                user=user, **arguments)
        return d

# --------------------------------------------------------------------------- #

    def del_location(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "del", request_path)
        d = d.addCallback(self.dbbroker.del_location, session=True,
                user=user, **arguments)
        return d

# --------------------------------------------------------------------------- #

    def make_aquilon(self, arguments, request_path, user):
        """This should do all the database work, then try to compile the
        file, and then finish or cancel the database transaction.

        Ultimately, the database work will actually pass back some sort
        of job/transaction id that the client could receive immediately,
        while the server continues to do the work.

        For now, this is just one long execution thread that the client
        will need to wait on.

        """

        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "make", request_path)
        # It gets very annoying trying to coordinate which methods need
        # to pass what variables into which other methods in the execution
        # chain.  Create a dictionary to pass along to each method that
        # can then access any of the transient variables.
        build_info = {}
        d = d.addCallback(self.dbbroker.make_aquilon, build_info,
                session=True, **arguments)
        d = d.addCallback(self.pbroker.create_tempdir, build_info)
        d = d.addCallback(self.template_creator.reconfigure, build_info,
                localhost=self.localhost, user=user, **arguments)
        d = d.addCallback(self.pbroker.compile_host, build_info,
                templatesdir=self.templatesdir, plenarydir=self.plenarydir,
                profilesdir=self.profilesdir, depsdir=self.depsdir,
                hostsdir=self.hostsdir, repdir=self.repdir)
        d = d.addBoth(self.pbroker.cleanup_tempdir, build_info)
        #d = d.addCallback(self.dbbroker.confirm_make, build_info, session=True)
        #d = d.addErrback(self.dbbroker.cancel_make, build_info, session=True)
        return d

# --------------------------------------------------------------------------- #

    def reconfigure(self, arguments, request_path, user):
        # Cut-n-paste from make aquilon, above, except for the
        # dbaccess call.
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "make", request_path)
        build_info = {}
        d = d.addCallback(self.dbbroker.verify_aquilon, build_info,
                session=True, **arguments)
        d = d.addCallback(self.pbroker.create_tempdir, build_info)
        d = d.addCallback(self.template_creator.reconfigure, build_info,
                localhost=self.localhost, user=user, **arguments)
        d = d.addCallback(self.pbroker.compile_host, build_info,
                templatesdir=self.templatesdir, plenarydir=self.plenarydir,
                profilesdir=self.profilesdir, depsdir=self.depsdir,
                hostsdir=self.hostsdir, repdir=self.repdir)
        d = d.addBoth(self.pbroker.cleanup_tempdir, build_info)
        return d

# --------------------------------------------------------------------------- #

    def sync(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "sync", request_path)
        d = d.addCallback(self.dbbroker.verify_domain, session=True,
                user=user, **arguments)
        d = d.addCallback(self.pbroker.sync,
                git_path=self.git_path, templatesdir=self.templatesdir,
                **arguments)
        # If no errors are raised from the commands, send a command back
        # to the client to execute.
        d = d.addCallback(lambda _:
                """env PATH="%s:$PATH" NO_PROXY=* git pull""" % self.git_path)
        return d

# --------------------------------------------------------------------------- #

    def get(self, arguments, request_path, user):
        # FIXME: Return absolute paths to git?
        # 1.0 just hard-codes the path modificatin into the client.
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "get", request_path)
        d = d.addCallback(self.dbbroker.verify_domain, session=True,
                user=user, **arguments)
        d = d.addCallback(lambda _: """env PATH="%(path)s:$PATH" NO_PROXY=* git clone '%(url)s/%(domain)s/.git' '%(domain)s' && cd '%(domain)s' && ( env PATH="%(path)s:$PATH" git checkout -b '%(domain)s' || true )""" % {"path":self.git_path, "url":self.git_templates_url, "domain":arguments["domain"]})
        return d

# --------------------------------------------------------------------------- #

    def add_domain(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "add", request_path)
        d = d.addCallback(self.dbbroker.add_domain, session=True,
                user=user, **arguments)
        d = d.addCallback(self.pbroker.add_domain, git_path=self.git_path,
                templatesdir=self.templatesdir, kingdir=self.kingdir,
                **arguments)
        return d

# --------------------------------------------------------------------------- #

    def del_domain(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "del", request_path)
        d = d.addCallback(self.dbbroker.del_domain, session=True,
                user=user, **arguments)
        d = d.addCallback(self.pbroker.del_domain,
                templatesdir=self.templatesdir, **arguments)
        return d

# --------------------------------------------------------------------------- #

    def put(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "put", request_path)
        d = d.addCallback(self.dbbroker.verify_domain, session=True,
                user=user, **arguments)
        # FIXME: Does the database need to be updated with this info?
        d = d.addCallback(self.pbroker.put, templatesdir=self.templatesdir,
                git_path=self.git_path, basedir=self.basedir,
                **arguments)
        return d

# --------------------------------------------------------------------------- #

    def deploy(self, arguments, request_path, user):
        arguments["fromdomain"] = arguments.pop("domain")
        arguments["todomain"] = arguments.pop("to")
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "deploy", request_path)
        d = d.addCallback(self.dbbroker.verify_domain, session=True,
                user=user, domain=arguments["fromdomain"], **arguments)
        # FIXME: Does the database need to be updated with this info?
        d = d.addCallback(self.pbroker.deploy, basedir=self.basedir,
                templatesdir=self.templatesdir, kingdir=self.kingdir,
                git_path=self.git_path, **arguments)
        return d

# --------------------------------------------------------------------------- #

    def status(self, arguments, request_path, user):
        stat = []
        # FIXME: Hard coded version number.
        stat.append("Aquilon Broker v1.1")
        stat.append("Server: %s" % self.localhost)
        stat.append("Database: %s" % self.dbbroker.safe_url)
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "show", request_path)
        d = d.addCallback(self.dbbroker.status, session=True, user=user,
                stat=stat, **arguments)
        d = d.addCallback(lambda _: stat)
        return d

# --------------------------------------------------------------------------- #

    def add_cpu(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "add", request_path)
        d = d.addCallback(self.dbbroker.add_cpu, session=True, **arguments)
        return d

# --------------------------------------------------------------------------- #

    def add_disk(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "add", request_path)
        d = d.addCallback(self.dbbroker.add_disk, session=True, **arguments)
        d = d.addCallback(self.template_creator.generate_plenary, user=user,
                plenarydir=self.plenarydir, localhost=self.localhost,
                **arguments)
        return d

# --------------------------------------------------------------------------- #

    def add_model(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "add", request_path)
        # NOTE: This does not try to verify that the model exists on the
        # filesystem anywhere.
        d = d.addCallback(self.dbbroker.add_model, session=True, **arguments)
        return d

# --------------------------------------------------------------------------- #

    def show_model(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "show", request_path)
        # NOTE: This does not try to verify that the model exists on the
        # filesystem anywhere.
        d = d.addCallback(self.dbbroker.show_model, session=True, **arguments)
        return d

# --------------------------------------------------------------------------- #

    def del_model(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "delete", request_path)
        # NOTE: This does not try to verify that the model exists on the
        # filesystem anywhere.
        d = d.addCallback(self.dbbroker.del_model, session=True, **arguments)
        return d

# --------------------------------------------------------------------------- #

    def pxeswitch(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "pxeswitch", request_path)
        d = d.addCallback(self.dbbroker.verify_host, session=True, user=user,
                **arguments)
        d = d.addCallback(self.pbroker.pxeswitch, **arguments)
        return d

# --------------------------------------------------------------------------- #

    def manage(self, arguments, request_path, user):
        """Associate a host with a domain."""

        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "manage", request_path)
        d = d.addCallback(self.dbbroker.verify_domain, session=True,
                user=user, **arguments)
        d = d.addCallback(self.dbbroker.manage, session=True, user=user,
                **arguments)
        return d

# --------------------------------------------------------------------------- #

    def add_machine(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "add", request_path)
        d = d.addCallback(self.dbbroker.add_machine, session=True, user=user,
                **arguments)
        d = d.addCallback(self.template_creator.generate_plenary, user=user,
                plenarydir=self.plenarydir, localhost=self.localhost,
                **arguments)
        return d

# --------------------------------------------------------------------------- #

    def show_machine(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "show", request_path)
        d = d.addCallback(self.dbbroker.show_machine, session=True, user=user,
                **arguments)
        return d

# --------------------------------------------------------------------------- #

    def del_machine(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "delete", request_path)
        d = d.addCallback(self.dbbroker.verify_machine, session=True,
                user=user, **arguments)
        d = d.addCallback(self.template_creator.remove_plenary, user=user,
                plenarydir=self.plenarydir, **arguments)
        d = d.addCallback(self.dbbroker.del_machine, session=True, user=user,
                **arguments)
        return d

# --------------------------------------------------------------------------- #

    def add_interface (self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "add", request_path)
        d = d.addCallback(self.dbbroker.add_interface, session=True, user=user,
                **arguments)
        d = d.addCallback(self.template_creator.generate_plenary, user=user,
                plenarydir=self.plenarydir, localhost=self.localhost,
                **arguments)
        return d

# --------------------------------------------------------------------------- #

    def del_interface(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "del", request_path)
        d = d.addCallback(self.dbbroker.del_interface, session=True, user=user,
                **arguments)
        d = d.addCallback(self.template_creator.generate_plenary, user=user,
                plenarydir=self.plenarydir, localhost=self.localhost,
                **arguments)
        return d

# --------------------------------------------------------------------------- #

    def show_host(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "show", request_path)
        d = d.addCallback(self.dbbroker.show_host, session=True,
                user=user, **arguments)
        return d

# --------------------------------------------------------------------------- #

    def show_host_all(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "show", request_path)
        d = d.addCallback(self.dbbroker.show_host_all, session=True,
                user=user, **arguments)
        return d

# --------------------------------------------------------------------------- #

    def add_host(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "add", request_path)
        d = d.addCallback(self.dbbroker.verify_domain, session=True,
                user=user, **arguments)
        d = d.addCallback(self.dbbroker.verify_add_host,
                session=True, user=user, **arguments)
        # FIXME: Should be re-enabled.
        #d = d.addCallback(self.pbroker.add_host, dsdb=self.dsdb, **arguments)
        d = d.addCallback(self.dbbroker.add_host, session=True, user=user,
                **arguments)
        d = d.addCallback(self.template_creator.generate_plenary, user=user,
                plenarydir=self.plenarydir, localhost=self.localhost,
                **arguments)
        return d

# --------------------------------------------------------------------------- #

    def del_host(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "del", request_path)
        d = d.addCallback(self.dbbroker.verify_del_host,
                session=True, user=user, **arguments)
        # FIXME: Should be re-enabled.
        #d = d.addCallback(self.pbroker.del_host, self.dsdb, **arguments)
        d = d.addCallback(self.dbbroker.del_host, session=True, user=user,
                **arguments)
        return d

# --------------------------------------------------------------------------- #

    def add_service (self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "put", request_path)
        d = d.addCallback(self.dbbroker.add_service, session = True,
                user = user, **arguments)
        return d
        
# --------------------------------------------------------------------------- #

    def show_service (self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "get", request_path)
        d = d.addCallback(self.dbbroker.show_service, session = True,
                user = user, **arguments)
        return d
        
# --------------------------------------------------------------------------- #

    def del_service (self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "del", request_path)
        d = d.addCallback(self.dbbroker.del_service, session = True,
                user = user, **arguments)
        return d
        
# --------------------------------------------------------------------------- #

    def bind_service (self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "bind", request_path)
        d = d.addCallback(self.dbbroker.bind_service, session=True,
                user=user, **arguments)
        return d
        
# --------------------------------------------------------------------------- #

    def unbind_service (self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "unbind", request_path)
        d = d.addCallback(self.dbbroker.unbind_service, session=True,
                user=user, **arguments)
        return d
        
# --------------------------------------------------------------------------- #

    def cat_hostname(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "cat", request_path)
        d = d.addCallback(self.dbbroker.verify_host, session=True, user=user,
                **arguments)
        d = d.addCallback(self.template_creator.cat_hostname,
                hostsdir=self.hostsdir, user=user, **arguments)
        return d
        
# --------------------------------------------------------------------------- #

    def cat_machine(self, arguments, request_path, user):
        d = defer.maybeDeferred(self.azbroker.check, None, user,
                "cat", request_path)
        d = d.addCallback(self.dbbroker.verify_machine, session=True, user=user,
                **arguments)
        d = d.addCallback(self.template_creator.cat_machine,
                plenarydir=self.plenarydir, user=user, **arguments)
        return d
        
# --------------------------------------------------------------------------- #

