#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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

import ms.version

ms.version.addpkg('lxml', '2.3.2')
ms.version.addpkg('argparse', '1.2.1')

import os
import sys
import argparse
from lxml import etree
from collections import defaultdict

was_error = False


def error(message):
    global was_error

    print >>sys.stderr, "ERROR: %s" % message
    was_error = True


def read_docbook(file, commands):
    cmd, xml = os.path.splitext(os.path.basename(file))

    try:
        tree = etree.parse(file)
    except etree.XMLSyntaxError, err:
        error("Failed to parse %s: %s" % (file, err))
        return

    tree.xinclude()

    # This code is somewhat depends on the style the existing documentation is
    # written. If the style changes considerably, then the code may need to be
    # adapted.
    ns = "http://docbook.org/ns/docbook"
    refsynopsisdiv = tree.find("{%s}refsynopsisdiv" % ns)
    if refsynopsisdiv is None:
        error("No refsynopsisdiv in %s. Maybe namespace is wrong?" % file)

    commands[cmd] = defaultdict(dict)

    # Collect all options mentioned in the synopsis
    # TODO: use xpath?
    for section in refsynopsisdiv.findall("{%s}cmdsynopsis" % ns):
        for option in section.getiterator("{%s}option" % ns):
            optname = option.text.strip()
            commands[cmd][optname]["docbook"] = True
            if option.findall("{%s}replaceable" % ns):
                commands[cmd][optname]["synopsis_has_arg"] = True

    # Collect all options described in a refsect1 titled "Options"
    # TODO: use xpath?
    for section in tree.findall("{%s}refsect1" % ns):
        title = section.find("{%s}title" % ns)
        if title.text.strip().lower() != "options":
            continue

        # Look for varlistentry/term/option
        # TODO: use xpath?
        for varentry in section.getiterator("{%s}varlistentry" % ns):
            term = varentry.find("{%s}term" % ns)
            for option in term.getiterator("{%s}option" % ns):
                optname = option.text.strip()
                commands[cmd][optname]["body"] = True
                if option.findall("{%s}replaceable" % ns):
                    commands[cmd][optname]["body_has_arg"] = True


def process_input_xml(file, commands, default_options):
    tree = etree.parse(file)
    for option in tree.xpath("command[@name='*']//option"):
        default_options["--" + option.attrib["name"]] = True

        if "reverse" in option.attrib:
            default_options["--" + option.attrib["reverse"]] = True
        elif option.attrib["type"] == "boolean":
            default_options["--no" + option.attrib["name"]] = True

        if "short" in option.attrib:
            default_options["-" + option.attrib["short"]] = True

    for section in tree.findall("command"):
        cmd = section.attrib["name"]
        if cmd == '*':
            # Definition of the global options, skip
            continue

        if cmd not in commands:
            # No DocBook documentation, skip
            continue

        for option in section.xpath(".//option"):
            optnames = ["--" + option.attrib["name"]]
            if "reverse" in option.attrib:
                optnames.append("--" + option.attrib["reverse"])
            elif option.attrib["type"] == "boolean":
                optnames.append("--no" + option.attrib["name"])

            for optname in optnames:
                commands[cmd][optname]["inputxml"] = True
                if option.attrib["type"] != "flag" and \
                   option.attrib["type"] != "boolean":
                    commands[cmd][optname]["inputxml_has_arg"] = True

        # TODO: merge default options into the command-specific options? That
        # would mean a bit more code here, but less special casing in
        # check_errors()


def check_errors(commands, default_options):
    for cmd in sorted(commands.keys()):
        for option, flags in sorted(commands[cmd].items()):
            if "docbook" not in flags and "body" in flags:
                error("Command %s, option %s is documented but not mentioned "
                      "in the synopsis." % (cmd, option))

            if "docbook" in flags and "body" not in flags:
                error("Command %s, option %s is mentioned in the synopsis, "
                      "but not described in the body." % (cmd, option))

            if "inputxml" in flags and "docbook" not in flags:
                error("Command %s, option %s is not documented." %
                      (cmd, option))

            if "inputxml" not in flags and \
               ("docbook" in flags or "body" in flags) and \
               option not in default_options:
                error("Command %s, option %s is documented, but does "
                      "not exist." % (cmd, option))

            if "synopsis_has_arg" in flags and "body_has_arg" not in flags:
                error("Command %s, option %s has an argument in the synopsis, "
                      "but not in the description." % (cmd, option))

            if "synopsis_has_arg" not in flags and "body_has_arg" in flags:
                error("Command %s, option %s has an argument in the "
                      "description, but not in the synopsis." % (cmd, option))

            if "inputxml_has_arg" in flags and not "synopsis_has_arg" in flags \
               and option not in default_options:
                error("Command %s, option %s has an argument in input.xml, "
                      "but not in the documentation." % (cmd, option))

            if "inputxml_has_arg" not in flags and "synopsis_has_arg" in flags \
               and option not in default_options:
                error("Command %s, option %s has an argument in the "
                      "synposis, but not in input.xml." % (cmd, option))


def main():
    _DIR = os.path.dirname(os.path.realpath(__file__))
    _ETCDIR = os.path.join(_DIR, "..", "etc")
    _DOCDIR = os.path.join(_DIR, "commands")

    parser = argparse.ArgumentParser(description='Documentation checker')
    parser.add_argument("--input_xml", default=os.path.join(_ETCDIR,
                                                            "input.xml"),
                        help="Location of input.xml")
    parser.add_argument("--command_dir", default=_DOCDIR,
                        help="Directory containing the command documentations")

    args = parser.parse_args()

    commands = defaultdict(dict)

    for file in os.listdir(args.command_dir):
        if not file.endswith(".xml"):
            continue
        read_docbook(os.path.join(args.command_dir, file), commands)

    default_options = {}
    process_input_xml(args.input_xml, commands, default_options)
    check_errors(commands, default_options)
    if was_error:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
