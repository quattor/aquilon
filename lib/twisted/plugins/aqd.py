# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Provide a twistd plugin for aqd to start up."""

import os
import sys

# This is done by the wrapper script.
# import aquilon.worker.depends

import coverage
from zope.interface import implements
from twisted.python import usage, log
from twisted.plugin import IPlugin
from twisted.application import strports
from twisted.application.service import IServiceMaker, MultiService
from twisted.internet import reactor

from aquilon.config import Config
from aquilon.twisted_patches import (GracefulProcessMonitor, integrate_logging)
from aquilon.worker.knc_protocol import KNCSite
from aquilon.worker.base_protocol import AQDSite

# This gets imported dynamically to avoid loading libraries before the
# config file has been parsed.
# from aquilon.worker.resources import RestServer


class Options(usage.Options):
    optFlags = [["noauth", None, "Do not start the knc listener."],
                ["authonly", None, "Only use knc, do not start an open port."],
                ["usesock", None, "use a unix socket to connect"]]
    optParameters = [["config", None, None, "Configuration file to use."],
                     ["coveragedir", None, None, "Code Coverage directory."],
                     ["coveragerc", None, None, "Coverage test config file."]]


def set_umask(config):
    os.umask(int(config.get("broker", "umask"), 8))


def set_thread_pool_size(config):
    # This is a somewhat made up number.  The default is ten.
    # We are resource-limited in 32-bit, can't just make this
    # a huge number.
    # We need at least 10 threads for the normal sqlalchemy
    # thread pool and 10 for the special "no locks allowed"
    # pool.  Anything beyond that are just being allowed to
    # queue and get themselves a logger.
    # We are also constrained by the number of knc sockets
    # that can be open at once (max file descriptors).
    pool_size = config.get("broker", "twisted_thread_pool_size")
    reactor.suggestThreadPoolSize(int(pool_size))


def make_required_dirs(config):
    for d in ["basedir", "profilesdir", "plenarydir", "rundir"]:
        dir = config.get("broker", d)
        if os.path.exists(dir):
            continue
        try:
            os.makedirs(dir)
        except OSError as e:
            log.msg("Could not create directory '%s': %s" % (dir, e))


class AQDMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "aqd"
    description = "Aquilon Daemon"
    options = Options

    def makeService(self, options):
        # Start up coverage ASAP.
        coverage_dir = options["coveragedir"]
        if coverage_dir:
            os.makedirs(coverage_dir, 0755)
            if options["coveragerc"]:
                coveragerc = options["coveragerc"]
            else:
                coveragerc = None
            self.coverage = coverage.coverage(config_file=coveragerc)
            self.coverage.erase()
            self.coverage.start()

        # Get the config object.
        config = Config(configfile=options["config"])

        # Helper for finishing off the coverage report.
        def stop_coverage():
            log.msg("Finishing coverage")
            self.coverage.stop()
            aquilon_srcdir = os.path.join(config.get("broker", "srcdir"),
                                          "lib", "aquilon")
            sourcefiles = []
            for dirpath, dirnames, filenames in os.walk(aquilon_srcdir):
                # FIXME: try to do this from the coverage config file
                if dirpath.endswith("aquilon"):
                    dirnames.remove("client")
                elif dirpath.endswith("aqdb"):
                    dirnames.remove("utils")

                for filename in filenames:
                    if not filename.endswith('.py'):
                        continue
                    sourcefiles.append(os.path.join(dirpath, filename))

            self.coverage.html_report(sourcefiles, directory=coverage_dir)
            self.coverage.xml_report(sourcefiles,
                                     outfile=os.path.join(coverage_dir, "aqd.xml"))

            with open(os.path.join(coverage_dir, "aqd.coverage"), "w") as outfile:
                self.coverage.report(sourcefiles, file=outfile)

        # Make sure the coverage report gets generated.
        if coverage_dir:
            reactor.addSystemEventTrigger('after', 'shutdown', stop_coverage)

        # Set this up before the aqdb libs get imported...
        integrate_logging(config)

        progname = os.path.split(sys.argv[0])[1]
        if progname == 'aqd':
            if config.get('broker', 'mode') != 'readwrite':
                log.msg("Broker started with aqd symlink, "
                        "setting config mode to readwrite")
                config.set('broker', 'mode', 'readwrite')
        if progname == 'aqd_readonly':
            if config.get('broker', 'mode') != 'readonly':
                log.msg("Broker started with aqd_readonly symlink, "
                        "setting config mode to readonly")
                config.set('broker', 'mode', 'readonly')
        log.msg("Loading broker in mode %s" % config.get('broker', 'mode'))

        # Dynamic import means that we can parse config options before
        # importing aqdb.  This is a hack until aqdb can be imported without
        # firing up database connections.
        resources = __import__("aquilon.worker.resources", globals(), locals(),
                               ["RestServer"], -1)
        RestServer = getattr(resources, "RestServer")
        restServer = RestServer(config)

        ResourcesCommandRegistry = getattr(resources, "ResourcesCommandRegistry")
        registry = ResourcesCommandRegistry(restServer)

        openSite = AQDSite(restServer)

        # twisted is nicely changing the umask for us when the process is
        # set to daemonize.  This sets it back.
        set_umask(config)
        reactor.addSystemEventTrigger('after', 'startup', set_umask, config)
        reactor.addSystemEventTrigger('after', 'startup',
                                      set_thread_pool_size, config)

        make_required_dirs(config)

        sockdir = config.get("broker", "sockdir")
        if not os.path.exists(sockdir):
            os.makedirs(sockdir, 0700)
        os.chmod(sockdir, 0700)

        if options["usesock"]:
            return strports.service("unix:%s/aqdsock" % sockdir, openSite)

        openport = config.get("broker", "openport")
        if config.has_option("broker", "bind_address"):
            bind_address = config.get("broker", "bind_address").strip()
            openaddr = "tcp:%s:interface=%s" % (openport, bind_address)
        else:  # pragma: no cover
            bind_address = None
            openaddr = "tcp:%s" % openport

        # Return before firing up knc.
        if options["noauth"]:
            return strports.service(openaddr, openSite)

        sockname = os.path.join(sockdir, "kncsock")
        # This flag controls whether or not this process will start up
        # and monitor knc.  Except for noauth mode knc has to be running,
        # but this process doesn't have to be the thing that starts it up.
        if config.getboolean("broker", "run_knc") or \
           config.getboolean("broker", "run_git_daemon"):
            mon = GracefulProcessMonitor()
            # FIXME: Should probably run krb5_keytab here as well.
            # and/or verify that the keytab file exists.
            if config.getboolean("broker", "run_knc"):
                keytab = config.get("broker", "keytab")
                knc_args = ["/usr/bin/env",
                            "KRB5_KTNAME=FILE:%s" % keytab,
                            config.get("kerberos", "knc"), "-lS", sockname]
                if bind_address:
                    knc_args.append("-a")
                    knc_args.append(bind_address)
                knc_args.append(config.get("broker", "kncport"))
                mon.addProcess("knc", knc_args)
            if config.getboolean("broker", "run_git_daemon"):
                # The git daemon *must* be invoked using the form 'git-daemon'
                # instead of invoking git with a 'daemon' argument.  The latter
                # will fork and exec git-daemon, resulting in a new pid that
                # the process monitor won't know about!
                gitpath = config.get("broker", "git_path")
                gitdaemon = config.get("broker", "git_daemon")
                ospath = os.environ.get("PATH", "")
                args = ["/usr/bin/env", "PATH=%s:%s" % (gitpath, ospath),
                        gitdaemon, "--export-all", "--base-path=%s" %
                        config.get("broker", "git_daemon_basedir")]
                if config.has_option("broker", "git_port"):
                    args.append("--port=%s" % config.get("broker", "git_port"))
                if bind_address:
                    args.append("--listen=%s" % bind_address)
                args.append(config.get("broker", "kingdir"))
                mon.addProcess("git-daemon", args)
            if config.getboolean("broker", "run_aqnotifyd"):
                notifyd = os.path.join(os.path.dirname(sys.argv[0]),
                                       "aq_notifyd")
                if not os.path.exists(notifyd):
                    notifyd = notifyd + ".py"
                args = [notifyd, "--config", config.baseconfig]
                mon.addProcess("notifyd", args, env=os.environ)
            mon.startService()
            reactor.addSystemEventTrigger('before', 'shutdown', mon.stopService)

        # This socket is created by twisted and only accessed by knc as
        # connections come in.
        if os.path.exists(sockname):
            try:
                log.msg("Attempting to remove old socket '%s'" % sockname)
                os.remove(sockname)
                log.msg("Succeeded removing old socket.")
            except OSError as e:
                log.msg("Could not remove old socket '%s': %s" % (sockname, e))

        unixsocket = "unix:%s" % sockname
        kncSite = KNCSite(restServer)

        multiService = MultiService()
        multiService.addService(strports.service(unixsocket, kncSite))
        if not options["authonly"]:
            multiService.addService(strports.service(openaddr, openSite))
        return multiService

serviceMaker = AQDMaker()
