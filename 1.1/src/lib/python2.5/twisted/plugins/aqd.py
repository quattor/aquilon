#!/ms/dist/python/PROJ/core/2.5/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''If you can read this, you should be Documenting'''

#import sys, os
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

from aquilon.server.resources import RestServer
from aquilon.server.kncwrappers import KNCSite
from aquilon.server.anonwrappers import AnonSite
from aquilon.server import dbaccess
from aquilon.server.authorization import AuthorizationBroker
from aquilon.server.broker import Broker, BrokerError

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
                ["usesock", None, "use a unix socket to connect"]
            ]
    optParameters = [
                ["kncport", "p", 6900, "The port number for knc to listen on."],
                ["openport", "p", 6901, "The port number to listen on for anonymous connections."],
                # For now, dburi must match dsn in aqdb.db.  (Backwards...)
                # ["dburi", "d", "sqlite", "DB URI to use."]
            ]

class AQDMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "aqd"
    description = "Aquilon Daemon"
    options = Options

    def makeService(self, options):
        #dburi = options["dburi"]
        #if options["dburi"] == 'sqlite':
        #        dburi = dbaccess.sqlite()
        from aquilon.aqdb.db import dsn as dburi

        dbbroker = dbaccess.DatabaseBroker(dburi)

        # We seem to be OK without something like this...
        #def initDatabase(dbbroker):
        #    def carryOn(_):
        #        print "Database Started", _
        #    return dbbroker.startup().addCallback(carryOn)
        #reactor.callWhenRunning(initDatabase, dbbroker)

        azbroker = AuthorizationBroker()

        # FIXME: This object should probably be handed a config file,
        # and then go off and create the dbbroker and azbroker...
        # (Or the RestServer could be handed the config, and then
        # create this object.)
        broker = Broker(dbbroker, azbroker)

        restServer = RestServer(broker)
        openSite = AnonSite(restServer)

        if options["usesock"]:
            return strports.service("unix:%s/aqdsock:mode=600"
                    % broker.basedir, openSite)

        if options["noknc"]:
            return strports.service(str(options["openport"]), openSite )

        sockname = broker.basedir + "/kncsock"
        mon = ProcessMonitor()
        # FIXME: Should probably run krb5_keytab here as well.
        # and/or verify that the keytab file exists.
        mon.addProcess("knc", ["/usr/bin/env",
            "KRB5_KTNAME=FILE:/var/spool/keytabs/%s" % broker.osuser,
            #"/ms/dev/kerberos/knc/1.3/install/exec/bin/knc",
            "/ms/dist/kerberos/PROJ/knc/prod/bin/knc",
            "-lS", sockname, str(options["kncport"]) ])
        mon.startService()
        reactor.addSystemEventTrigger('before', 'shutdown', mon.stopService)

        unixsocket = "unix:%s:mode=600" % sockname
        kncSite = KNCSite( restServer )

        # FIXME: Not sure if we want to do this... if not, just
        # go back to returning strports.service() for a single
        # service.
        multiService = MultiService()
        multiService.addService( strports.service( unixsocket, kncSite ) )
        multiService.addService( strports.service( str(options["openport"]), openSite ) )
        return multiService

serviceMaker = AQDMaker()
