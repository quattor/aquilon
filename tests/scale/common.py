#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Some common utilities used by the scale tests."""


import os
import signal
import sys
from subprocess import Popen

from aquilon.config import Config


class TestRack(object):
    def __init__(self, building, rackid):
        self.building = building
        self.rackid = rackid
        self.row = building[0]
        self.column = rackid

    def get_rack(self):
        return "%s%s" % (self.building, self.rackid)

    def get_tor_switch(self, half):
        return "%s%sgd1r%02d.one-nyp.ms.com" % (self.building,
                                                self.rackid, half)

    def get_machine(self, half, offset):
        return "%s%ss1%02dp%d" % (self.building, self.rackid, half, offset)

    def get_host(self, half, offset):
        return "scaletest%d.one-nyp.ms.com" % (100*self.rackid+48*half+offset)


class TestNetwork(object):
    networks = [[8, 8, 4, [  1,  65]],
                [8, 8, 4, [129, 193]],
                [8, 8, 5, [  1,  65]],
                [8, 8, 5, [129, 193]],
                [8, 8, 6, [  1,  65]],
                [8, 8, 6, [129, 193]],
                [8, 8, 7, [  1,  65]],
                [8, 8, 7, [129, 193]]]

    def __init__(self, network, half):
        self.first = self.networks[network][0]
        self.second = self.networks[network][1]
        self.third = self.networks[network][2]
        self.fourth = self.networks[network][3][half]

    def get_mac(self, offset):
        return "02:02:%02x:%02x:%02x:%02x" % (
                self.first, self.second, self.third, self.fourth + offset + 8)

    def get_ip(self, offset):
        return "%d.%d.%d.%d" % (
                self.first, self.second, self.third, self.fourth + offset + 8)


class AQRunner(object):
    def __init__(self, aq=None, host=None, port=None, aqservice=None):
        self.aq = aq or os.path.realpath(os.path.join(
            os.path.dirname(__file__), '..', '..', 'bin', 'aq'))
        #self.aq = aq or "/ms/dist/aquilon/PROJ/aqd/prod/bin/aq"
        #self.host = host or "oyidb1622"
        self.host = host or None
        self.port = port or None
        self.aqservice = aqservice or None

    def run(self, args, **kwargs):
        full_args = [str(self.aq)]
        full_args.extend([str(arg) for arg in args])
        if self.host:
            full_args.append("--aqhost")
            full_args.append(str(self.host))
        if self.port:
            full_args.append("--aqport")
            full_args.append(str(self.port))
        if self.aqservice:
            full_args.append("--aquser")
            full_args.append(str(self.aqservice))
        if not kwargs.has_key("stdout"):
            kwargs["stdout"] = 1
        if not kwargs.has_key("stderr"):
            kwargs["stderr"] = 2
        return Popen(full_args, **kwargs)

    def wait(self, args, **kwargs):
        p = self.run(args, **kwargs)
        p.wait()
        return p.returncode


class AQBroker(object):
    default_dir = os.path.dirname(__file__)
    default_twistd = os.path.realpath(os.path.join(default_dir,
                                                   '..', '..',
                                                   'bin', 'twistd'))
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
        aqdbdir = os.path.join(self.config.get("broker", "srcdir"), "lib",
                               "python2.5", "aquilon", "aqdb")
        cmdlst = ['./utils/build_db.py', '--populate'] 
        p = Popen(cmdlst, stdout=1, stderr=2, env=env, cwd=aqdbdir)
        rc = p.wait()


#if __name__=='__main__':
