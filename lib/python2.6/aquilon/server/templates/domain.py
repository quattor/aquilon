# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
import logging

from aquilon.config import Config
from aquilon.exceptions_ import (ArgumentError, ProcessException)
from aquilon.server.processes import run_command
from aquilon.server.templates.index import build_index
from aquilon.server.locks import lock_queue, CompileKey
from aquilon.aqdb.model import Host, Cluster
from aquilon.server.logger import CLIENT_INFO

LOGGER = logging.getLogger('aquilon.server.templates.domain')

class TemplateDomain(object):

    def __init__(self, dom, logger=LOGGER):
        self.domain = dom
        self.logger = logger

    def directories(self):
        """Return a list of directories required for compiling this domain"""
        config = Config()
        dirs = []
        dirs.append(os.path.join(config.get("broker", "templatesdir"),
                    self.domain.name))

        dirs.append(os.path.join(config.get("broker", "quattordir"),
                                 "cfg",
                                 "domains",
                                 self.domain.name))
              
        dirs.append(os.path.join(config.get("broker", "quattordir"),
                                 "build",
                                 "xml",
                                 self.domain.name))

        return dirs

    def outputdirs(self):
        """Returns a list of directories that should exist before compiling"""
        config = Config()
        dirs = []
        dirs.append(config.get("broker", "profilesdir"))
        # The regression tests occasionally have issues with panc
        # auto-creating this directory - not sure why.
        if self.domain.clusters:
            dirs.append(os.path.join(config.get("broker", "quattordir"),
                                     "build", "xml", self.domain.name,
                                     "clusters"))
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

        self.logger.info("preparing domain %s for compile" % self.domain.name)

        # Ensure that the compile directory is in a good state.
        config = Config()
        outputdir = config.get("broker", "profilesdir")

        for d in self.directories() + self.outputdirs():
            if not os.path.exists(d):
                try:
                    self.logger.info("creating %s" % d)
                    os.makedirs(d, mode=0770)
                except OSError, e:
                    raise ArgumentError("Failed to mkdir %s: %s" % (d, e))

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
        args.append("%s/build.xml" %
                    config.get("broker", "compiletooldir"))
        args.append("-Dbasedir=%s" % config.get("broker", "quattordir"))
        args.append("-Dpanc.jar=%s" % self.domain.compiler)
        args.append("-Dpanc.formatter=%s" %
                    config.get("broker", "panc_formatter"))
        args.append("-Ddomain=%s" % self.domain.name)
        args.append("-Ddistributed.profiles=%s" %
                    config.get("broker", "profilesdir"))
        args.append("-Dpanc.batch.size=%s" %
                    config.get("broker", "panc_batch_size"))
        args.append("-Dant-contrib.jar=%s" %
                    config.get("broker", "ant_contrib_jar"))
        if (only):
            # Use -Dforce.build=true?
            args.append("-Dobject.profile=%s" % only)
            args.append("compile.object.profile")
        else:
            # Technically this is the default, but being explicit
            # doesn't hurt.
            args.append("compile.domain.profiles")

        out = ''
        try:
            if not locked:
                # FIXME: The git workflow branch has a more sophisticated
                # notion of objectlist... revisit this in that branch.
                key = CompileKey(domain=self.domain.name, logger=self.logger)
                lock_queue.acquire(key)
            self.logger.info("starting compile")
            try:
                out = run_command(args, env=panc_env, logger=self.logger,
                                  path=config.get("broker", "quattordir"),
                                  loglevel=CLIENT_INFO)
            except ProcessException, e:
                raise ArgumentError("\n%s%s" % (e.out, e.err))
        finally:
            if not locked:
                lock_queue.release(key)

        # No need for a lock here - there is only a single file written
        # and it is swapped into place atomically.
        build_index(config, session, config.get("broker", "profilesdir"),
                    logger=self.logger)
        return out
