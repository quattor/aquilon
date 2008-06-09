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


global_defaults = {
    """ The user variable, since it can be overridden by a config file,
        is not meant in any way, shape, or form to be used for security.
        Having it be something that can be overridden by an env variable
        is just an extra layer of convenience. """

            "user"     : os.environ.get("USER"),

    """ srcdir is only used by unit tests at the moment, but maybe useful for
        scripts that want to execute stand-alone. """

            "srcdir"   : os.path.realpath(os.path.join(
                            os.path.dirname(__file__), "..", "..", "..")),

            "hostname" : socket.gethostname(),
        }


class Config(SafeConfigParser):
    """ All defaults should be in etc/aqd.conf.defaults.  This is only needed to
        supply defaults that are determined by code at run time. It is set up
        with 'Borg' idiom semantics, i.e. instantiated if none exists yet, but
        if there is one already, any "new" config object will have all the same
        info as any other """

    __shared_state = {}
    def __init__(self, defaults=global_defaults, configfile=None):
        self.__dict__ = self.__shared_state
        if getattr(self, "baseconfig", None):
            if not configfile or self.baseconfig == configfile:
                return
            raise AquilonError("Could not configure with %s, already configured with %s" %
                    (configfile, self.baseconfig))

        """ This is a small race condition here... baseconfig could be
            checked here, pre-empted, checked again elsewhere, and also
            get here.  If that ever happens, it is only a problem if one
            passed in a configfile and the other didn't.  Punting for now. """

        if configfile:
            self.baseconfig = configfile
        else:
            self.baseconfig = os.environ.get("AQDCONF", "/etc/aqd.conf")
        SafeConfigParser.__init__(self, defaults)
        src_defaults = os.path.join(defaults["srcdir"],
                "etc", "aqd.conf.defaults")
        read_files = self.read([src_defaults, self.baseconfig])
        # FIXME: Check that read_files includes the files we asked for...

        """ Allow a section to "pull in" another section, as though all the
            values defined in the alternate were actually defined there. """

        for section in self.sections():
            section_option = "%s_section" %section
            if self.has_option(section, section_option):
                alternate_section = self.get(section, section_option, raw=True) #TODO: True, or get raw
                if self.has_section(alternate_section):
                    for (name, value) in self.items(alternate_section):
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
