#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018  Contributor
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
import sys
from six.moves.configparser import SafeConfigParser  # pylint: disable=F0401

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


def lookup_file_path(name, check_conf_in_sources=False):
    """
    Return the full path of a data file.

    If we're running from the source tree and check_conf_in_sources=True,
    returns the source tree path only if the config file exists. Default
    is to return it unconditionally.
    """
    if  running_from_source():
        source_config_path = os.path.join(_SRCDIR, "etc", name)
        if os.path.exists(source_config_path) or not check_conf_in_sources:
            return source_config_path

    paths_to_try = [os.path.join("/etc", "aquilon", name),
                    os.path.join("/usr", "share", "aquilon", "etc", name),
                    os.path.join(_SRCDIR, "../../../aqd-vcs/prod/etc", name),
                    os.path.join(_SRCDIR, "etc", name)]
    for path in paths_to_try:
        if os.path.exists(path):
            return path

    # We know it does not exist, but returning the name may give the user a
    # clue
    return paths_to_try[0]


def amend_sys_path(config):
    """
    Amend sys path to change which python modules will be loaded
    If application running in unittest mode, prepend
    fakepython module dir to replace modules used for tests
    :param config:
    :return:
    """
    if config.has_value('unittest', 'fake_module_location'):
        sys.path = [config.get('unittest', 'fake_module_location')] + sys.path


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


class NewStyleClassSafeConfigParser(object, SafeConfigParser):
    pass


class Config(NewStyleClassSafeConfigParser):
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

    def lookup_tool(self, prog):
        key = prog.replace('-', '_')
        if self.has_value("tool_locations", key):
            return self.get("tool_locations", key)
        # If no override was specified, we rely on $PATH lookup
        return prog

    def lookup_tool_timeout(self, prog):
        key = prog.replace('-', '_').split('/')[-1]

        if self.has_value("tool_timeout", key):
            timeout_value = int(self.get("tool_timeout", key))
        elif self.getboolean("tool_timeout", "default_enabled"):
            timeout_value = int(self.get("tool_timeout", "default_value"))
        else:
            timeout_value = 0
        return timeout_value

    def has_value(self, section, key):
        if self.has_section(section) and \
                self.has_option(section, key) and \
                self.get(section, key):
            return True
        return False

    def getboolean(self, section, option, default=False):
        if not self.has_section(section):
            return default
        if not self.has_value(section, option):
            return default
        return super(Config, self).getboolean(section, option)