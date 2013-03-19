#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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
"""
Parse AQD configuration
"""

import sys
import os
from ConfigParser import NoSectionError, NoOptionError

import ms.version
ms.version.addpkg('argparse', '1.1')

import argparse

BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
SRCDIR = os.path.join(BINDIR, "..")
LIBDIR = os.path.join(SRCDIR, "lib", "python2.6")

sys.path.append(LIBDIR)

from aquilon.config import Config


def list_all(config):
    defaults = {}
    for name, value in config.items("DEFAULT"):
        defaults[name] = value

    for name in sorted(defaults.keys()):
        value = config.get("DEFAULT", name)
        print "DEFAULT.%s=%s" % (name, value)

    for section in sorted(config.sections()):
        for name in sorted(config.options(section)):
            value = config.get(section, name)

            # Defaults are copied into every section. Skip them unless the
            # value has been overridden
            if name in defaults and value == defaults[name]:
                continue

            # Skip section inclusion directive
            if name == "%s_section" % section:
                continue

            print "%s.%s=%s" % (section, name, value)


def get_option(config, key):
    if "." not in key:
        raise SystemExit("The key must have the syntax SECTION.OPTION.")
    section, name = key.split('.', 1)
    try:
        print config.get(section, name)
    except NoSectionError:
        raise SystemExit("No such section: %s" % section)
    except NoOptionError:
        raise SystemExit("No such option in section %s: %s" % (section, name))


def main():
    parser = argparse.ArgumentParser(description="Parse AQD configuration")
    parser.add_argument("-c", "--config", dest="config", action="store",
                        help="parse the given config file instead of the default")
    parser.add_argument("--get", metavar="SECTION.NAME", action="store",
                        help="get the value of the specified configuration key")
    parser.add_argument("--list", action="store_true",
                        help="list all defined configuration options and their values")

    opts = parser.parse_args()

    config = Config(configfile=opts.config)

    if opts.get:
        get_option(config, opts.get)
    elif opts.list:
        list_all(config)
    else:
        raise SystemExit("Please specify an action.")


if __name__ == "__main__":
    main()
