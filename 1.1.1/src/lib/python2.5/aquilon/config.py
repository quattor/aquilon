#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Basic config module for aqdb and the broker."""

import os
import sys
import socket
import re
from ConfigParser import SafeConfigParser

from exceptions_ import AquilonError

# Only used by unit tests at the moment, but maybe useful for scripts that
# want to execute stand-alone.
def _get_srcdir():
    """Determine the location of the binaries/source code being used."""
    bindir = os.path.dirname(os.path.realpath(sys.argv[0]))
    m = re.match(
            r"(/ms(?:/.(global|local)/[^/]+)?/dist/aquilon/PROJ/aqd/[^/+]).*?",
            bindir)
    if m:
        return m.group(1)
    m = re.match(r"(.*/aquilon/aqd/[^/+]/[^/+]).*?", bindir)
    if m:
        return m.group(1)
    # Hmm... shot in the dark...
    m = re.match(r"(.*/src)(/.*?|)$", bindir)
    if m:
        return m.group(1)
    # Giving up.
    return bindir

global_defaults = {
            #TODO: can we make this pwd.getpwuid(os.getuid())[0]? (or euid?)
            "user"     : os.environ.get("USER"),
            "basedir"  : "/var/quattor",
            "srcdir"   : _get_srcdir(),
            "hostname" : socket.gethostname(),
        }

config_defaults = {
        "database": {
            "dbdir"       : "%(basedir)s/aquilondb",
            "dbfile"      : "%(dbdir)s/aquilon.db",
            "dsn"         : "sqlite:///%(dbfile)s",
            "dblogfile"   : "%(dbdir)s/aqdb.log",

            "ora_version" : "10.2.0.1.0",
            "ora_home"    : "/ms/dist/orcl/PROJ/product/%(ora_version)s",
            "export"      : "%(ora_home)s/bin/exp",
            "exportlog"   : "/tmp/aqdb_export.log",
            "import"      : "%(ora_home)s/bin/imp",

            "user"        : "USER", #stub
            "dsn"         : "oracle://%(user)s:PASSWORD@%(server)s",
            "connect_str" : "%(user)s/%(user)s@%(server)s",
            "dumpfile"    : "/tmp/%(user)s.dmp",
        },
        "broker": {
            "quattordir"        : "%(basedir)s",
            "servername"        : "%(hostname)s",
            "umask"             : "0022",
            "kncport"           : "6900",
            "openport"          : "6901",
            "templateport"      : "%(openport)s",
            "git_templates_url" : "http://%(servername)s:%(templateport)s/templates",
            "kingdir"           : "%(quattordir)s/template-king",
            "templatesdir"      : "%(quattordir)s/templates",
            "rundir"            : "%(quattordir)s/run",
            "logdir"            : "%(quattordir)s/logs",
            "logfile"           : "%(logdir)s/aqd.log",
            "html_access_log"   : "%(logdir)s/aqd_access_log",
            "profilesdir"       : "%(quattordir)s/web/htdocs/profiles",
            "depsdir"           : "%(quattordir)s/deps",
            "hostsdir"          : "%(quattordir)s/hosts",
            "plenarydir"        : "%(quattordir)s/plenary",
            "swrepdir"          : "%(quattordir)s/swrep",
            "git_path"          : "/ms/dist/fsf/PROJ/git/1.5.4.2/bin",
            "git"               : "%(git_path)s/git",
            "dsdb"              : "/ms/dist/aurora/PROJ/dsdb/4.4.2/bin/dsdb",
            "knc"               : "/ms/dist/kerberos/PROJ/knc/1.4/bin/knc",
        },
    }


class Config(SafeConfigParser):
    # Any "new" config object will have all the same info as any other.
    __shared_state = {}
    def __init__(self, defaults=global_defaults, configfile=None):
        self.__dict__ = self.__shared_state
        if getattr(self, "baseconfig", None):
            if not configfile or self.baseconfig == configfile:
                return
            raise AquilonError("Could not configure with %s, already configured with %s" %
                    (configfile, self.baseconfig))
        # This is a small race condition here... baseconfig could be
        # checked here, pre-empted, checked again elsewhere, and also
        # get here.  If that ever happens, it is only a problem if one
        # passed in a configfile and the other didn't.  Punting for now.
        if configfile:
            self.baseconfig = configfile
        else:
            self.baseconfig = os.environ.get("AQDCONF", "/etc/aqd.conf")
        SafeConfigParser.__init__(self, defaults)
        self.read(self.baseconfig)
        for (section, defaults) in config_defaults.items():
            if not self.has_section(section):
                self.add_section(section)
            for (name, value) in defaults.items():
                if not self.has_option(section, name):
                    self.set(section, name, value)


if __name__=='__main__':
    config = Config()
    print "[DEFAULT]"
    for (name, value) in config.defaults().items():
        print "%s=%s" % (name, value)
    for section in config.sections():
        print "[%s]" % section
        for (name, value) in config.items(section):
            print "%s=%s" % (name, value)
