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

from aquilon.server.processes import ProcessBroker
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
        self.osuser = os.environ.get('USER')
        self.basedir = "/var/tmp/%s/quattor" % self.osuser
        self.profilesdir = "%s/web/htdocs/profiles" % self.basedir
        self.depsdir = "%s/deps" % self.basedir
        self.hostsdir = "%s/hosts" % self.basedir
        self.templatesdir = "%s/templates" % self.basedir
        self.kingdir = "%s/template-king" % self.basedir
        self.default_domain = ".ms.com"
        self.git_path = "/ms/dist/fsf/PROJ/git/1.5.4.2/bin"
        self.git = "%s/git" % self.git_path
        self.htpasswd = "/ms/dist/elfms/PROJ/apache/2.2.6/bin/htpasswd"
        self.cdpport = 7777
        self.localhost = socket.gethostname()
        self.git_templates_url = "http://%s:6901/templates" % self.localhost
        self.domain_name = "production"

# --------------------------------------------------------------------------- #

    def show_location(self, **kwargs):
        # just a facade method
        return self.dbbroker.show_location(session=True, **kwargs)

# --------------------------------------------------------------------------- #

    def show_location_type(self, **kwargs):
        # just a facade method
        return self.dbbroker.show_location_type(session=True, **kwargs)

# --------------------------------------------------------------------------- #

    def add_location(self, **kwargs):
        return self.dbbroker.add_location(session=True, **kwargs)

# --------------------------------------------------------------------------- #

    def del_location(self, **kwargs):
        return self.dbbroker.del_location(session=True, **kwargs)

# --------------------------------------------------------------------------- #

    def make_aquilon(self, **kwargs):
        """This should do all the database work, then try to compile the
        file, and then finish or cancel the database transaction.

        Ultimately, the database work will actually pass back some sort
        of job/transaction id that the client could receive immediately,
        while the server continues to do the work.

        For now, this is just one long execution thread that the client
        will need to wait on.

        """

        d = self.dbbroker.make_aquilon(session=True, **kwargs)
        d = d.addCallback(self.pbroker.make_aquilon, basedir=self.basedir)
        d = d.addCallback(self.dbbroker.confirm_make, session=True)
        d = d.addErrback(self.dbbroker.cancel_make, session=True)
        return d

# --------------------------------------------------------------------------- #

    def sync (self, **kwargs):
        d = self.dbbroker.verify_domain(session=True,
                domain=kwargs.pop("domain"))
        d = d.addCallback(self.pbroker.sync,
                git_path=self.git_path, templatesdir=self.templatesdir,
                **kwargs)
        d = d.addCallback(lambda _:
                """env PATH="%s:$PATH" NO_PROXY=* git pull""" % self.git_path)
        return d

# --------------------------------------------------------------------------- #

    def get (self, domain, **kwargs):
        # FIXME: Return absolute paths to git?
        # 1.0 just hard-codes the path modificatin into the client.
        return """env PATH="%(path)s:$PATH" NO_PROXY=* git clone '%(url)s/%(domain)s/.git' '%(domain)s' && cd '%(domain)s' && ( env PATH="%(path)s:$PATH" git checkout -b '%(domain)s' || true )""" % {"path":self.git_path, "url":self.git_templates_url, "domain":domain}

# --------------------------------------------------------------------------- #

    def add_domain (self, **kwargs):
        d = self.dbbroker.add_domain(session=True, **kwargs)
        d = d.addCallback(self.pbroker.add_domain, git_path=self.git_path,
                templatesdir=self.templatesdir, kingdir=self.kingdir,
                **kwargs)
        return d

# --------------------------------------------------------------------------- #

    def del_domain (self, **kwargs):
        d = self.dbbroker.del_domain(session=True, **kwargs)
        d = d.addCallback(self.pbroker.del_domain,
                templatesdir=self.templatesdir, **kwargs)
        return d

# --------------------------------------------------------------------------- #

    def put (self, **kwargs):
        # FIXME: Does the database need to be updated with this info?
        d = self.pbroker.put(templatesdir=self.templatesdir,
                git_path=self.git_path, basedir=self.basedir, **kwargs)
        return d

# --------------------------------------------------------------------------- #

    def deploy (self, **kwargs):
        # FIXME: Does the database need to be updated with this info?
        # For now, just verify that the domain exists.
        d = self.dbbroker.verify_domain(session=True,
                domain=kwargs.pop("fromdomain"))
        d = d.addCallback(self.pbroker.deploy, basedir=self.basedir,
                templatesdir=self.templatesdir, kingdir=self.kingdir,
                git_path=self.git_path, **kwargs)
        return d

# --------------------------------------------------------------------------- #

    def status(self, **kwargs):
        stat = []
        # FIXME: Hard coded version number.
        stat.append("Aquilon Broker v1.1")
        d = self.dbbroker.status(session=True, stat=stat, **kwargs)
        d = d.addCallback(lambda _: stat)
        return d

# --------------------------------------------------------------------------- #

    def add_model (self, name, vendor, hardware, machine):
        return self.dbbroker.add_model(name, vendor, hardware, machine, session=True)

# --------------------------------------------------------------------------- #

    def pxeswitch (self, host, **kwargs):
        return self.pbroker.pxeswitch(host, **kwargs)

