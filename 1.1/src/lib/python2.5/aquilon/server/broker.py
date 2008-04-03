#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon

import sys
import os
import os.path
import shutil
import socket
from  aquilon.server.dbaccess import DatabaseBroker

#=============================================================================#

class BrokerError (StandardError):
    def __init__ (self):
        self.errorList = []

    def errorMessage (self):
        return "\n".join(self.errorList)

    def pushError (self, errorMessage):
        self.errorList.append(errorMessage)

#=============================================================================#

class Broker(object):
    def __init__(self, dbbroker, azbroker):
        self.dbbroker = dbbroker
        self.azbroker = azbroker
        self.osuser = os.environ.get('USER')
        self.basedir = "/var/tmp/%s/quattor" % self.osuser
        self.profilesdir = "%s/web/htdocs/profiles" % self.basedir
        self.depsdir = "%s/deps" % self.basedir
        self.hostsdir = "%s/hosts" % self.basedir
        self.templatesdir = "%s/templates" % self.basedir
        self.default_domain = ".ms.com"
        self.git_path = "/ms/dist/fsf/PROJ/git/1.5.4.2/bin"
        self.git = "%s/git" % self.git_path
        self.htpasswd = "/ms/dist/elfms/PROJ/apache/2.2.6/bin/htpasswd"
        self.cdpport = 7777
        self.localhost = socket.gethostname()
        self.git_templates_url = "http://%s:6901/templates" % self.localhost
        self.domain_name = "production"

# --------------------------------------------------------------------------- #

    def show_location (self, **kwargs):
        # just a facade method
        return self.dbbroker.showLocation(**kwargs)

# --------------------------------------------------------------------------- #

    def show_location_type (self, **kwargs):
        # just a facade method
        return self.dbbroker.showLocationType(**kwargs)

# --------------------------------------------------------------------------- #

    def add_location (self, **kwargs):
        return self.dbbroker.addLocation (**kwargs)

# --------------------------------------------------------------------------- #

    def del_location (self, **kwargs):
        return self.dbbroker.delLocation(**kwargs)

# --------------------------------------------------------------------------- #
    
    def make_aquilon (self, **kwargs):
        return ""
