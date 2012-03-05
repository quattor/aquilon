# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
import re

from aquilon.config import Config
from aquilon.exceptions_ import ArgumentError, ProcessException, InternalError
from aquilon.worker.processes import run_command, run_git
from aquilon.worker.templates.index import build_index
from aquilon.worker.locks import lock_queue, CompileKey
from aquilon.aqdb.model import Host, Cluster
from aquilon.worker.logger import CLIENT_INFO

LOGGER = logging.getLogger(__name__)


class TemplateDomain(object):

    def __init__(self, domain, author=None, logger=LOGGER):
        self.domain = domain
        self.author = author
        self.logger = logger

    def directories(self):
        """Return a list of directories required for compiling this domain"""
        config = Config()
        dirs = []

        if self.domain.branch_type == 'domain':
            dirs.append(os.path.join(config.get("broker", "domainsdir"),
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

    def compile(self, session, only=None, locked=False,
                panc_debug_include=None, panc_debug_exclude=None,
                cleandeps=False):
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

        config = Config()

        if self.domain.branch_type == 'sandbox':
            if not self.author:
                raise InternalError("Missing required author to compile "
                                    "sandbox %s" % self.domain.name)
            sandboxdir = os.path.join(config.get("broker", "templatesdir"),
                                      self.author.name, self.domain.name)
            if not os.path.exists(sandboxdir):
                raise ArgumentError("Sandbox directory '%s' does not exist." %
                                    sandboxdir)
            if not self.sandbox_has_latest(config, sandboxdir):
                self.logger.warn("Sandbox %s/%s does not contain the "
                                 "latest changes from the prod domain.  If "
                                 "there are failures try "
                                 "`git fetch && git merge origin/prod`" %
                                 (self.author.name, self.domain.name))

        self.logger.info("preparing domain %s for compile" % self.domain.name)

        # Ensure that the compile directory is in a good state.
        outputdir = config.get("broker", "profilesdir")

        for d in self.directories() + self.outputdirs():
            if not os.path.exists(d):
                try:
                    self.logger.info("creating %s" % d)
                    os.makedirs(d)
                except OSError, e:
                    raise ArgumentError("Failed to mkdir %s: %s" % (d, e))

        if only:
            objectlist = only.split(' ')
        else:
            q = session.query(Host)
            q = q.filter_by(branch=self.domain, sandbox_author=self.author)
            hosts = q.all()
            q = session.query(Cluster)
            q = q.filter_by(branch=self.domain, sandbox_author=self.author)
            clusters = q.all()
            objectlist = hosts + clusters
            if self.author:
                # Need to restrict to the subset of the sandbox managed
                # by this author.
                only = " ".join([h.fqdn for h in hosts] +
                                ["cluster/%s" % c.name for c in clusters])

        if (len(objectlist) == 0):
            return 'no hosts: nothing to do'

        # The ant wrapper is silly and it may pick up the wrong set of .jars if
        # ANT_HOME is not set
        panc_env = {"PATH": "%s/bin:%s" % (config.get("broker", "java_home"),
                                           os_environ.get("PATH", "")),
                    "ANT_HOME": config.get("broker", "ant_home"),
                    "JAVA_HOME": config.get("broker", "java_home")}
        if config.has_option("broker", "ant_options"):
            panc_env["ANT_OPTS"] = config.get("broker", "ant_options")

        args = [config.get("broker", "ant")]
        args.append("--noconfig")
        args.append("-f")
        args.append("%s/build.xml" %
                    config.get("broker", "compiletooldir"))
        args.append("-Dbasedir=%s" % config.get("broker", "quattordir"))
        args.append("-Dpanc.jar=%s" % self.domain.compiler)
        args.append("-Dpanc.formatter=%s" %
                    config.get("panc", "formatter"))
        args.append("-Ddomain=%s" % self.domain.name)
        args.append("-Ddistributed.profiles=%s" % outputdir)
        args.append("-Dpanc.batch.size=%s" %
                    config.get("panc", "batch_size"))
        args.append("-Dant-contrib.jar=%s" %
                    config.get("broker", "ant_contrib_jar"))
        args.append("-Dgzip.output=%s" %
                    config.get("panc", "gzip_output"))
        if self.domain.branch_type == 'sandbox':
            args.append("-Ddomain.templates=%s" % sandboxdir)
        if (only):
            # Use -Dforce.build=true?
            args.append("-Dobject.profile=%s" % only)
            args.append("compile.object.profile")
        else:
            # Technically this is the default, but being explicit
            # doesn't hurt.
            args.append("compile.domain.profiles")
        if panc_debug_include is not None:
            args.append("-Dpanc.debug.include=%s" % panc_debug_include)
        if panc_debug_exclude is not None:
            args.append("-Dpanc.debug.exclude=%s" % panc_debug_exclude)
        if cleandeps:
            # Cannot send a false value - the test in build.xml is for
            # whether or not the property is defined at all.
            args.append("-Dclean.dep.files=%s" % cleandeps)

        out = ''
        try:
            if not locked:
                if only and len(objectlist) == 1:
                    key = CompileKey(domain=self.domain.name, profile=only,
                                     logger=self.logger)
                else:
                    key = CompileKey(domain=self.domain.name,
                                     logger=self.logger)
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
        build_index(config, session, outputdir, logger=self.logger)
        return out

    def sandbox_has_latest(self, config, sandboxdir):
        domainsdir = config.get('broker', 'domainsdir')
        prod_domain = config.get('broker', 'default_domain_start')
        proddir = os.path.join(domainsdir, prod_domain)
        try:
            prod_commit = run_git(['rev-list', '-n', '1', 'HEAD'],
                                  path=proddir, logger=self.logger).strip()
        except ProcessException:
            prod_commit = ''
        if not prod_commit:
            raise InternalError("Error finding top commit for %s" %
                                prod_domain)
        filterre = re.compile('^' + prod_commit + '$')
        try:
            found_latest = run_git(['rev-list', 'HEAD'], path=sandboxdir,
                                   logger=self.logger, filterre=filterre)
        except ProcessException:
            self.logger.warn("Failed to run git command in sandbox %s." %
                             sandboxdir)
            found_latest = ''
        return bool(found_latest)
