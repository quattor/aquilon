#!/usr/bin/env python
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
"""Convenience methods for manipulating the broker used for testing."""


import os
import signal
import sys
from subprocess import Popen

if __name__=='__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', "lib")))

from aquilon.config import Config
from aquilon.exceptions_ import ProcessException


class AQBroker(object):
    default_dir = os.path.dirname(__file__)
    default_aqd = os.path.realpath(os.path.join(default_dir,
                                                   '..', '..',
                                                   'sbin', 'aqd.py'))
    default_configfile = os.path.realpath(os.path.join(default_dir,
                                                       'aqd.conf.scale'))

    def __init__(self, aqd=None, configfile=None):
        self.aqd = aqd or self.default_aqd
        self.configfile = configfile or self.default_configfile
        self.config = Config(configfile=self.configfile)
        self.pidfile = os.path.join(self.config.get("broker", "rundir"),
                                    "aqd.pid")
        self.logfile = self.config.get("broker", "logfile")
        self.coverage = os.path.join(self.config.get("broker", "logdir"),
                                     "aqd.coverage")

    def start(self, **kwargs):
        """Start a broker with the given config."""
        # FIXME: Make coverage configurable.
        args = [self.aqd, "--pidfile", self.pidfile,
                "--logfile", self.logfile,
                "aqd",
                # "--coverage", self.coverage,
                "--config", self.configfile]
        p = Popen(args, stdout=1, stderr=2)
        return p.wait()

    def stop(self, **kwargs):
        """Attempt to stop a running broker."""
        if os.path.exists(self.pidfile):
            f = file(self.pidfile)
            pid = f.readline()
            f.close()
            os.kill(int(pid), signal.SIGTERM)

    def get_aqservice(self):
        return self.config.get("broker", "service")

    def initialize(self, **kwargs):
        """Clear out and set up the base directory and database.
        
        Most of this was ripped straight from runtests.py.
        
        """
        p = Popen(self.config.get("kerberos", "krb5_keytab"),
                  stdout=1, stderr=2)
        if p.wait():
            raise ProcessException(code=p.returncode)

        for label in ["quattordir", "swrepdir", ]:
            dir = self.config.get("broker", label)
            if os.path.exists(dir):
                continue
            try:
                os.makedirs(dir)
            except OSError, e:
                print >>sys.stderr, "Could not create %s: %s" % (dir, e)
        
        dirs = []
        if self.config.has_option("database", "dbfile"):
            dirs.append(os.path.dirname(self.config.get("database", "dbfile")))
        for label in ["domainsdir", "kingdir", "rundir", "profilesdir",
                      "plenarydir", "logdir"]:
            dirs.append(self.config.get("broker", label))
        
        for dir in dirs:
            if os.path.exists(dir):
                print "Removing %s" % dir
                p = Popen(("/bin/rm", "-rf", dir), stdout=1, stderr=2)
                if p.wait():
                    raise ProcessException(code=p.returncode)
            try:
                os.makedirs(dir)
            except OSError, e:
                print >>sys.stderr, "Could not create %s: %s" % (dir, e)
        
        template_source = "git://nyaqd1/quattor/template-king"
        template_dest = self.config.get("broker", "kingdir")
        env = {}
        env["PATH"] = "%s:%s" % (self.config.get("broker", "git_path"),
                                 os.environ.get("PATH", ""))
        p = Popen(("git", "clone", "--bare", "--branch", "prod",
                   template_source, template_dest),
                  env=env, stdout=1, stderr=2)
        if p.wait():
            raise ProcessException(code=p.returncode)
        
        # FIXME: Maybe make a new perftest section in the conf...
        swrep_base = self.config.get("database", "password_base")
        p = Popen(("rsync", "-avP", "--delete", "-e",
                   "ssh -q -o StrictHostKeyChecking=no " +
                   "-o UserKnownHostsFile=/dev/null -o BatchMode=yes",
                   os.path.join(swrep_base, "swrep", "repository"),
                   self.config.get("broker", "swrepdir")),
                  stdout=1, stderr=2)
        if p.wait():
            raise ProcessException(code=p.returncode)

        env = {}
        for (key, value) in os.environ.items():
            env[key] = value
        env["AQDCONF"] = self.configfile
        aqdbdir = os.path.join(self.config.get("broker", "srcdir"),
                               "tests", "aqdb")
        cmdlst = ['./build_db.py', '--delete', '--populate', 'data/unittest.dump']
        p = Popen(cmdlst, stdout=1, stderr=2, env=env, cwd=aqdbdir)
        if p.wait():
            raise ProcessException(code=p.returncode)
        cmdlst = ['./add_admin.py']
        p = Popen(cmdlst, stdout=1, stderr=2, env=env, cwd=aqdbdir)
        if p.wait():
            raise ProcessException(code=p.returncode)


if __name__=='__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-b", "--start", dest="start", action="store_true",
                      default=False, help="Start the broker.")
    parser.add_option("-r", "--stop", dest="stop", action="store_true",
                      default=False, help="Stop the broker.")
    parser.add_option("-s", "--config", dest="config", type="string",
                      help="The configfile to use")
    (options, args) = parser.parse_args()

    broker = AQBroker(options.config)
    if options.stop:
        broker.stop()
    if options.start:
        broker.start()

