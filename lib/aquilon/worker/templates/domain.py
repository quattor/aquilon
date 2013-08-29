# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Any work by the broker to write out (or read in?) templates lives here."""


import os
from os import environ as os_environ
import logging
import re

from aquilon.config import Config
from aquilon.exceptions_ import ArgumentError, ProcessException, InternalError
from aquilon.aqdb.model import (Host, Cluster, Fqdn, DnsRecord, HardwareEntity,
                                Machine)
from aquilon.worker.logger import CLIENT_INFO
from aquilon.notify.index import trigger_notifications
from aquilon.worker.processes import run_command, run_git
from aquilon.worker.locks import lock_queue, CompileKey

LOGGER = logging.getLogger(__name__)


class TemplateDomain(object):

    def __init__(self, domain, author=None, logger=LOGGER):
        super(TemplateDomain, self).__init__()

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
        list or set containing the profiles that need to be compiled.

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

        nothing_to_do = True
        if only:
            nothing_to_do = False
        else:
            hostnames = session.query(Fqdn)
            hostnames = hostnames.join(DnsRecord, HardwareEntity, Machine, Host)
            hostnames = hostnames.filter_by(branch=self.domain,
                                            sandbox_author=self.author)

            clusternames = session.query(Cluster.name)
            clusternames = clusternames.filter_by(branch=self.domain,
                                                  sandbox_author=self.author)
            if self.author:
                # Need to restrict to the subset of the sandbox managed
                # by this author.
                only = [str(fqdn) for fqdn in hostnames]
                only.extend(["cluster/%s" % c.name for c in clusternames])
                nothing_to_do = not bool(only)
            else:
                nothing_to_do = not hostnames.count() and not clusternames.count()

        if nothing_to_do:
            return 'No hosts: nothing to do.'

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
        args.append("-Dpanc.template_extension=%s" %
                    config.get("panc", "template_extension"))
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
        if only:
            # Use -Dforce.build=true?
            # TODO: pass the list in a temp file
            args.append("-Dobject.profile=%s" % " ".join(only))
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
                if only and len(only) == 1:
                    key = CompileKey(domain=self.domain.name,
                                     profile=list(only)[0],
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

        trigger_notifications(config, self.logger, CLIENT_INFO)
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
