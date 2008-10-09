#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Any work by the broker to write out (or read in?) templates lives here."""

import os
from os import path as os_path, environ as os_environ
from datetime import datetime

from twisted.python import log

from aquilon.config import Config
from aquilon.exceptions_ import (ArgumentError, ProcessException,
                                 IncompleteError)
from aquilon.server.processes import run_command, build_index
from aquilon.server.templates.base import compileLock, compileRelease
from aquilon.server.templates.host import PlenaryHost


class TemplateDomain(object):

    def __init__(self):
        pass

    def compile(self, session, domain, user, only=None):
        """flush all host templates within a domain and trigger a
        recompile. The build directories are checked and constructed
        if neccessary, so no prior setup is required.  The compile may
        take some time (current rate is 10 hosts per second, with a
        couple of seconds of constant overhead), and the possibility
        of blocking on the compile lock.

        If the 'only' parameter is provided, then it should be a
        single host object and just that host will be compiled. The
        domain parameter should be of Domain class, and must match the
        domain of the host specified by the only parameter (if
        provided).  The 'user' is the username requesting the compile
        and is purely used as information to annotate any output
        files.

        May raise ArgumentError exception, else returns the standard
        output (as a string) of the compile
        """

        log.msg("preparing domain %s for compile"%domain.name)

        # Ensure that the compile directory is in a good state.
        config = Config()
        outputdir = config.get("broker", "profilesdir")
        builddir = config.get("broker", "builddir")
        profiledir = "%s/domains/%s/profiles"% (builddir, domain.name)
        if not os.path.exists(profiledir):
            try:
                os.makedirs(profiledir, mode=0770)
            except OSError, e:
                raise ArgumentError("failed to mkdir %s: %s" % (builddir, e))

        # Check that all host templates are up-to-date
        # XXX: This command could take many minutes, it'd be really
        # nice to be able to give progress messages to the user
        try:
            compileLock()

            if (only):
                hl = [ only ]
            else:
                hl = domain.hosts
            if (len(hl) == 0):
                return 'no hosts: nothing to do'

            log.msg("flushing %d hosts"%len(hl))
            for h in hl:
                p = PlenaryHost(h)
                try:
                    p.write(profiledir, user, locked=True)
                except IncompleteError, e:
                    pass
                    #log.msg("Encountered incomplete host: %s" % e)

            domaindir = os_path.join(config.get("broker", "templatesdir"), domain.name)
            includes = [domaindir,
                        config.get("broker", "plenarydir"),
                        config.get("broker", "swrepdir")]

            panc_env={"PATH":"%s:%s" % (config.get("broker", "javadir"),
                                        os_environ.get("PATH", ""))}
            
            args = [ "/ms/dist/fsf/PROJ/make/prod/bin/gmake" ]
            args.append("-f")
            args.append("%s/GNUmakefile.build" % config.get("broker", "compiletooldir"))
            args.append("MAKE=%s -f %s"%(args[0], args[2]))
            args.append("DOMAIN=%s"%domain.name)
            args.append("TOOLDIR=%s"%config.get("broker", "compiletooldir"))
            args.append("QROOT=%s"%config.get("broker", "quattordir"))
            args.append("PANC=%s"%config.get("broker", "panc"))
            if (only):
                args.append("only")
                args.append("HOST=%s"%only.fqdn)

            out = ''
            log.msg("starting compile")
            try:
                out = run_command(args, env=panc_env, path=config.get("broker", "quattordir"))
            except ProcessException, e:
                raise ArgumentError("\n%s%s"%(e.out,e.err))

        finally:
            compileRelease();

        build_index(config, session, outputdir)
        return out


#if __name__=='__main__':
