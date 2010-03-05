#!/usr/bin/env python2.6
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
"""Convenience methods for manipulating the broker used for testing."""


import os
import signal
import sys
from subprocess import Popen

if __name__=='__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..',
                                                     "lib", "python2.6")))

from aquilon.config import Config


class AQBroker(object):
    default_dir = os.path.dirname(__file__)
    default_twistd = os.path.realpath(os.path.join(default_dir,
                                                   '..', '..',
                                                   'bin', 'twistd.py'))
    default_configfile = os.path.realpath(os.path.join(default_dir,
                                                       'aqd.conf.scale'))

    def __init__(self, twistd=None, configfile=None):
        self.twistd = twistd or self.default_twistd
        self.configfile = configfile or self.default_configfile
        self.config = Config(configfile=self.configfile)
        self.pidfile = os.path.join(self.config.get("broker", "rundir"),
                                    "aqd.pid")
        self.logfile = self.config.get("broker", "logfile")

    def start(self, **kwargs):
        """Start a broker with the given config."""
        args = [self.twistd, "--pidfile", self.pidfile,
                "--logfile", self.logfile,
                "aqd", "--config", self.configfile]
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
        return self.config.get("broker", "user")

    def initialize(self, **kwargs):
        """Clear out and set up the base directory and database.
        
        Most of this was ripped straight from runtests.py.
        
        """
        if not os.path.exists("/var/spool/keytabs/%s" % \
           self.config.get("broker", "user")):
            p = Popen(("/ms/dist/kerberos/PROJ/krb5_keytab/"
                       "prod/sbin/krb5_keytab"),
                       stdout=1, stderr=2)
            rc = p.wait()

        for label in ["quattordir", "kingdir", "swrepdir", ]:
            dir = self.config.get("broker", label)
            if os.path.exists(dir):
                continue
            try:
                os.makedirs(dir)
            except OSError, e:
                print >>sys.stderr, "Could not create %s: %s" % (dir, e)
        
        dirs = [self.config.get("database", "dbdir")]
        for label in ["templatesdir", "rundir", "logdir", "profilesdir",
                "depsdir", "hostsdir", "plenarydir", ]:
            dirs.append(self.config.get("broker", label))
        
        for dir in dirs:
            if os.path.exists(dir):
                print "Removing %s" % dir
                p = Popen(("/bin/rm", "-rf", dir), stdout=1, stderr=2)
                rc = p.wait()
                # FIXME: check rc
            try:
                os.makedirs(dir)
            except OSError, e:
                print >>sys.stderr, "Could not create %s: %s" % (dir, e)
        
        #template_king_host = self.config.get("unittest", "template_king_host")
        template_king_host = "nyaqd1"
        p = Popen(("rsync", "-avP", "-e", "ssh", "--delete",
            "%s:/var/quattor/template-king" % template_king_host,
            # Minor hack... ignores config kingdir...
            self.config.get("broker", "quattordir")),
            stdout=1, stderr=2)
        rc = p.wait()
        # FIXME: check rc
        
        #swrep_repository_host = self.config.get("unittest", "swrep_repository_host")
        swrep_repository_host = "nyaqd1"
        p = Popen(("rsync", "-avP", "-e", "ssh", "--delete",
            "%s:/var/quattor/swrep/repository" % swrep_repository_host,
            self.config.get("broker", "swrepdir")),
            stdout=1, stderr=2)
        rc = p.wait()
        # FIXME: check rc

        env = {}
        for (key, value) in os.environ.items():
            env[key] = value
        env["AQDCONF"] = self.configfile
        aqdbdir = os.path.join(self.config.get("broker", "srcdir"),
                               "tests", "aqdb")
        cmdlst = ['./build_db.py', '--delete', '--populate']
        p = Popen(cmdlst, stdout=1, stderr=2, env=env, cwd=aqdbdir)
        rc = p.wait()


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

