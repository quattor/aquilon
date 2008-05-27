#!/ms/dist/python/PROJ/core/2.5/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Provide a twistd plugin for aqd to start up."""

import os
#import sys
#
#sys.path.append( os.path.join(
#            os.path.dirname( os.path.realpath(sys.argv[0]) ),
#            "..", "lib", "python2.5" ) )

import aquilon.server.depends

from zope.interface import implements
from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application import strports
from twisted.application.service import IServiceMaker, MultiService
from twisted.runner.procmon import ProcessMonitor
from twisted.internet import reactor

from aquilon.config import Config
#from aquilon.server.resources import RestServer
from aquilon.server.kncwrappers import KNCSite
from aquilon.server.anonwrappers import AnonSite

#from aquilon.aqdb.utils.Debug import ipshell

#from twisted.application import service
#from twisted.web import server
## Define the application/service that twisted will run.  Boilerplate.
## TODO: port (and log directory, debug verbosity, etc.) should be out
## in a config file somewhere.
#restServer = RestServer()
#application = service.Application( "aqd" )
#serviceCollection = service.IServiceCollection( application )
##restSite = KNCSite( restServer )
#restSite = server.Site( restServer )
#restService = strports.service( "6900", restSite )
#restService.setServiceParent( application )

class Options(usage.Options):
    optFlags = [
                ["noknc", None, "Do not start the knc listener."],
                ["usesock", None, "use a unix socket to connect"],
            ]
    optParameters = [
                ["config", None, "Configuration file to use."],
            ]

class AQDMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "aqd"
    description = "Aquilon Daemon"
    options = Options

    def makeService(self, options):
        config = Config(configfile=options["config"])
        # Dynamic import means that we can parse config options before
        # importing aqdb.  This is a hack until aqdb can be imported without
        # firing up database connections.
        resources = __import__("aquilon.server.resources", globals(), locals(),
                ["RestServer"], -1)
        RestServer = getattr(resources, "RestServer")

        restServer = RestServer(config)
        openSite = AnonSite(restServer)

        if options["usesock"]:
            return strports.service("unix:%s/aqdsock:mode=600"
                    % config.get("broker", "basedir"), openSite)

        if options["noknc"]:
            return strports.service(config.get("broker", "openport"), openSite)

        sockname = os.path.join(config.get("broker", "rundir"), "kncsock")
        mon = ProcessMonitor()
        # FIXME: Should probably run krb5_keytab here as well.
        # and/or verify that the keytab file exists.
        mon.addProcess("knc", ["/usr/bin/env",
            "KRB5_KTNAME=FILE:/var/spool/keytabs/%s"
            % config.get("broker", "user"),
            config.get("broker", "knc"), "-lS", sockname,
            config.get("broker", "kncport")])
        mon.startService()
        reactor.addSystemEventTrigger('before', 'shutdown', mon.stopService)

        unixsocket = "unix:%s:mode=600" % sockname
        kncSite = KNCSite( restServer )

        # FIXME: Not sure if we want to do this... if not, just
        # go back to returning strports.service() for a single
        # service.
        multiService = MultiService()
        multiService.addService(strports.service(unixsocket, kncSite))
        multiService.addService(strports.service(
            config.get("broker", "openport"), openSite))
        return multiService

serviceMaker = AQDMaker()
