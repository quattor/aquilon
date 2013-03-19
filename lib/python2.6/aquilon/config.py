#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Basic config module for aqdb and the broker."""

import os
import socket
import pwd
from ConfigParser import SafeConfigParser

from aquilon.exceptions_ import AquilonError


def get_username():
    return pwd.getpwuid(os.getuid()).pw_name

# All defaults should be in etc/aqd.conf.defaults.  This is only needed to
# supply defaults that are determined by code at run time.
global_defaults = {
            # The user variable, since it can be overridden by a config file,
            # is not meant in any way, shape, or form to be used for security.
            # Having it be something that can be overridden by an env variable
            # is just an extra layer of convenience.
            "user": os.environ.get("USER") or get_username(),
            # Only used by unit tests at the moment, but maybe useful for
            # scripts that want to execute stand-alone.
            "srcdir": os.path.realpath(os.path.join(
                            os.path.dirname(__file__), "..", "..", "..")),
            "hostname": socket.getfqdn(),
        }


class Config(SafeConfigParser):
    """ Supplies configuration to the broker and database engines
        Set up as a borg/singleton class (can only be instanced once) """

    __shared_state = {}

    def __init__(self, defaults=global_defaults, configfile=None):
        self.__dict__ = self.__shared_state
        if getattr(self, "baseconfig", None):
            if not configfile or self.baseconfig == os.path.realpath(configfile):
                return
            raise AquilonError("Could not configure with %s, already configured with %s" %
                    (configfile, self.baseconfig))
        # This is a small race condition here... baseconfig could be
        # checked here, pre-empted, checked again elsewhere, and also
        # get here.  If that ever happens, it is only a problem if one
        # passed in a configfile and the other didn't.  Punting for now.
        if configfile:
            self.baseconfig = os.path.realpath(configfile)
        else:
            self.baseconfig = os.path.realpath(
                    os.environ.get("AQDCONF", "/etc/aqd.conf"))
        SafeConfigParser.__init__(self, defaults)
        src_defaults = os.path.join(defaults["srcdir"],
                "etc", "aqd.conf.defaults")
        read_files = self.read([src_defaults, self.baseconfig])
        for file in [src_defaults, self.baseconfig]:
            if file not in read_files:
                raise AquilonError("Could not read configuration file %s." % file)

        # Allow a section to "pull in" another section, as though all the
        # values defined in the alternate were actually defined there.
        for section in self.sections():
            section_option = "%s_section" % section
            if self.has_option(section, section_option):
                alternate_section = self.get(section, section_option)
                if self.has_section(alternate_section):
                    for (name, value) in self.items(alternate_section):
                        self.set(section, name, value)
