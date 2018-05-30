# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018 Contributor
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

import re
from xml.etree import ElementTree

from six import iteritems

from aquilon.config import lookup_file_path

# Regular Expression for matching variables in a path definition.
# Currently only supports stuffing a single variable in a path
# component.


class CommandEntry(object):
    """Representation of a single command in the registry.

    For each transport defined for a command in input.xml a command entry
    will be created.
    """
    def __init__(self, fullname, method, path, name, trigger):
        self.fullname = fullname
        self.method = method
        self.path = path
        self.name = name
        self.trigger = trigger

    def add_option(self, option_name, paramtype, enumtype=None):
        """Add an option to a command.

        This function is called for each option tag found within a
        command defined in input.xml.  Note it will be repeated for
        each transport.
        """
        pass

    def add_format(self, format, style):
        """Add a format to a command.

        This function is called for each format tag found within a
        command defined in inpux.xml.  Note it will be repeated for
        each transport.
        """
        pass


class CommandRegistry(object):

    def new_entry(self, fullname, method, path, name, trigger):
        """Create a new CommandEntry"""
        return CommandEntry(fullname, method, path, name, trigger)

    def add_entry(self, entry):
        """Save the completed CommandEntry"""
        pass

    def __init__(self):
        self._commands_cache = {}
        self._readonly_commands = []
        self._commands_options = {}
        tree = ElementTree.parse(lookup_file_path("input.xml"))

        for command in tree.getiterator("command"):
            if 'name' not in command.attrib:
                continue
            name = command.attrib['name']
            self._commands_options[name] = set()
            for transport in command.getiterator("transport"):
                if "method" not in transport.attrib or \
                   "path" not in transport.attrib:
                    log.msg("Warning: incorrect transport specification "
                            "for %s." % name)
                    continue

                method = transport.attrib["method"]
                path = transport.attrib["path"]
                trigger = transport.attrib.get("trigger")

                fullname = name
                if trigger:
                    fullname = fullname + "_" + trigger

                entry = self.new_entry(fullname, method, path, name, trigger)
                if not entry:
                    continue

                for option in command.getiterator("option"):
                    if 'name' not in option.attrib or \
                       'type' not in option.attrib:
                        log.msg("Warning: incorrect options specification "
                                "for %s." % fullname)
                        continue
                    option_name = option.attrib["name"]
                    paramtype = option.attrib["type"]
                    enumtype = option.attrib.get("enum")
                    entry.add_option(option_name, paramtype, enumtype)

                for format in command.getiterator("format"):
                    if "name" not in format.attrib:
                        log.msg("Warning: incorrect format specification "
                                "for %s." % fullname)
                        continue
                    style = format.attrib["name"]
                    entry.add_format(format, style)

                self.add_entry(entry)

                self._commands_cache[fullname] = {"command": name,
                                                  "option": trigger}
                self._commands_options[name].add(trigger)

                if name.startswith('show') or name.startswith('search') or \
                   name.startswith('cat') or name == 'status' or \
                   name == 'dump_dns':
                    self._readonly_commands.append(fullname)
