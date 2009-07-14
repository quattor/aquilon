# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Any work by the broker to write out (or read in?) templates lives here."""


import os
from os import environ as os_environ

from twisted.python import log

from aquilon.config import Config
from aquilon.exceptions_ import (ArgumentError, ProcessException)
from aquilon.server.processes import run_command
from aquilon.server.templates.index import build_index
from aquilon.server.templates.base import compileLock, compileRelease
from aquilon.aqdb.model import Host, Cluster


class TemplateDomain(object):

    def __init__(self, dom):
        self.domain = dom

    def directories(self):
        """Return a list of directories required for compiling this domain"""
        config = Config()
        dirs = []
        dirs.append(os.path.join(config.get("broker", "templatesdir"),
                    self.domain.name))

        dirs.append(os.path.join(config.get("broker", "quattordir"),
                                 "deps",
                                 self.domain.name))

        dirs.append(os.path.join(config.get("broker", "quattordir"),
                                 "cfg",
                                 "domains",
                                 self.domain.name))
              
        dirs.append(os.path.join(config.get("broker", "quattordir"),
                                 "build",
                                 "xml",
                                 self.domain.name))

        dirs.append(os.path.join(config.get("broker", "quattordir"),
                                 "build",
                                 "clusters",
                                 self.domain.name))
        return dirs

    def outputdirs(self):
        """Returns a list of directories that should exist before compiling"""
        config = Config()
        dirs = []
        dirs.append(config.get("broker", "profilesdir"))
        dirs.append(config.get("broker", "clustersdir"))
        return dirs

    def compile(self, session, only=None, locked=False):
        """The build directories are checked and constructed
        if necessary, so no prior setup is required.  The compile may
        take some time (current rate is 10 hosts per second, with a
        couple of seconds of constant overhead), and the possibility
        of blocking on the compile lock.

        If the 'only' parameter is provided, then it should be a
        single object and just that profile will be compiled.

        May raise ArgumentError exception, else returns the standard
        output (as a string) of the compile
        """

        log.msg("preparing domain %s for compile"%self.domain.name)

        # Ensure that the compile directory is in a good state.
        config = Config()
        outputdir = config.get("broker", "profilesdir")

        for d in self.directories() + self.outputdirs():
            if not os.path.exists(d):
                try:
                    log.msg("creating %s"%d)
                    os.makedirs(d, mode=0770)
                except OSError, e:
                    raise ArgumentError("failed to mkdir %s: %s" % (d, e))

        # XXX: This command could take many minutes, it'd be really
        # nice to be able to give progress messages to the user
        try:
            if (not locked):
                compileLock()

            if (only):
                objectlist = [ only ]
            else:
                objectlist = self.domain.hosts

            if (len(objectlist) == 0):
                return 'no hosts: nothing to do'

            panc_env = {"PATH":"%s:%s" % (config.get("broker", "javadir"),
                                          os_environ.get("PATH", ""))}
            
            args = [config.get("broker", "ant")]
            args.append("-f")
            args.append("%s/build.xml" % config.get("broker", "compiletooldir"))
            args.append("-Dbasedir=%s" % config.get("broker", "quattordir"))
            args.append("-Dpanc.jar=%s" % self.domain.compiler)
            args.append("-Ddomain=%s" % self.domain.name)
            args.append("-Ddistributed.profiles=%s" % config.get("broker", "profilesdir"))
            args.append("-Dpanc.batch.size=%s" %
                        config.get("broker", "panc_batch_size"))
            if (only):
                # Use -Dforce.build=true?
                args.append("-Dobject.profile=%s" % only)
                args.append("compile.object.profile")
            else:
                # Technically this is the default, but being explicit
                # doesn't hurt.
                args.append("compile.domain.profiles")

            out = ''
            log.msg("starting compile")
            try:
                out = run_command(args, env=panc_env,
                                  path=config.get("broker", "quattordir"))
            except ProcessException, e:
                raise ArgumentError("\n%s%s" % (e.out, e.err))

        finally:
            if (not locked):
                compileRelease()

        build_index(config, session, config.get("broker", "profilesdir"))
        return out


