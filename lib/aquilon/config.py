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
"""Basic config module for aqdb and the broker."""

import os
import socket
import pwd
from ConfigParser import SafeConfigParser

from aquilon.exceptions_ import AquilonError

_SRCDIR = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                        "..", ".."))


def get_username():
    return pwd.getpwuid(os.getuid()).pw_name


def running_from_source():
    """
    Determine if we're running from the source tree.

    Being able to run from the source tree makes development easier, but the
    directory structure may differ from the installed system, and also some
    settings should have different defaults. Use this function when such
    decisions are needed to be made.
    """

    # Need a file that is guaranteed not to be installed - Makefile is a
    # reasonable choice
    return os.path.exists(os.path.join(_SRCDIR, "Makefile"))


def lookup_file_path(name):
    """
    Return the full path of a data file.

    If we're running from the source tree, then use the default files;
    otherwise, use the system-wide ones.
    """
    if running_from_source():
        return os.path.join(_SRCDIR, "etc", name)

    paths_to_try = [os.path.join("/etc", "aquilon", name),
                    os.path.join("/usr", "share", "aquilon", "etc", name),
                    os.path.join(_SRCDIR, "etc", name)]
    for path in paths_to_try:
        if os.path.exists(path):
            return path

    # We know it does not exist, but returning the name may give the user a
    # clue
    return paths_to_try[0]


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
    "srcdir": _SRCDIR,
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
            raise AquilonError("Could not configure with %s, already "
                               "configured with %s" %
                               (configfile, self.baseconfig))
        # This is a small race condition here... baseconfig could be
        # checked here, pre-empted, checked again elsewhere, and also
        # get here.  If that ever happens, it is only a problem if one
        # passed in a configfile and the other didn't.  Punting for now.
        if configfile:
            self.baseconfig = os.path.realpath(configfile)
        else:
            self.baseconfig = os.path.realpath(os.environ.get("AQDCONF",
                                                              "/etc/aqd.conf"))
        SafeConfigParser.__init__(self, defaults)
        src_defaults = lookup_file_path("aqd.conf.defaults")
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
