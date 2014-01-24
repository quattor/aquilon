#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014  Contributor
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
"""
Compile templates outside of the broker

This script is inteded to be used primarily by the template unit test. It could
be extended later if that turns out to be useful.
"""

from __future__ import print_function

import sys
import os
from subprocess import call

import ms.version
ms.version.addpkg('argparse', '1.2.1')

import argparse

# -- begin path_setup --
BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
LIBDIR = os.path.join(BINDIR, "..", "lib")

if LIBDIR not in sys.path:
    sys.path.append(LIBDIR)
# -- end path_setup --

from aquilon.config import Config, lookup_file_path


def run_domain_compile(options, config):
    panc_env = os.environ.copy()

    if config.has_option("tool_locations", "ant_home"):
        ant_home = config.get("tool_locations", "ant_home")
        panc_env["PATH"] = "%s/bin:%s" % (ant_home, panc_env.get("PATH", ""))
        # The ant wrapper is silly and it may pick up the wrong set of .jars if
        # ANT_HOME is not set
        panc_env["ANT_HOME"] = ant_home

    if config.has_option("tool_locations", "java_home"):
        java_home = config.get("tool_locations", "java_home")
        panc_env["PATH"] = "%s/bin:%s" % (java_home, panc_env.get("PATH", ""))
        panc_env["JAVA_HOME"] = java_home

    if config.has_option("broker", "ant_options"):
        panc_env["ANT_OPTS"] = config.get("broker", "ant_options")

    args = [config.lookup_tool("ant"), "--noconfig", "-f"]
    args.append(lookup_file_path("build.xml"))
    args.append("-Dbasedir=%s" % options.basedir)

    if options.swrep:
        args.append("-Dswrep=%s" % options.swrep)

    if options.panc_jar:
        panc = options.panc_jar
    else:
        panc = config.get("panc", "pan_compiler")
    args.append("-Dpanc.jar=%s" % panc)

    if options.compress_output:
        compress_suffix = ".gz"
    else:
        compress_suffix = ""

    formats = []
    suffixes = []

    if options.xml_output is None:
        options.xml_output = config.getboolean("panc", "xml_profiles")
    if options.json_output is None:
        options.json_output = config.getboolean("panc", "json_profiles")

    if options.xml_output:
        formats.append("pan" + compress_suffix)
        suffixes.append(".xml" + compress_suffix)
    if options.json_output:
        formats.append("json" + compress_suffix)
        suffixes.append(".json" + compress_suffix)

    args.append("-Dpanc.formats=%s" % ",".join(formats))
    args.append("-Dprofile.suffixes=%s" % ",".join(suffixes))
    args.append("-Dpanc.template_extension=%s" %
                config.get("panc", "template_extension"))
    args.append("-Ddomain.templates=%s" % options.templates)
    args.append("-Ddomain=%s" % options.domain)

    if options.batch_size:
        args.append("-Dpanc.batch.size=%d" % options.batch_size)
    else:
        args.append("-Dpanc.batch.size=%s" % config.get("panc", "batch_size"))

    print("Running %s" % " ".join(args))
    return call(args, env=panc_env, cwd=options.basedir)


def main():
    parser = argparse.ArgumentParser(description="Compile templates")
    parser.add_argument("-c", "--config", dest="config", action="store",
                        help="location of the config file",
                        default=lookup_file_path("aqd.conf.defaults"))
    parser.add_argument("--basedir", action="store", required=True,
                        help="base directory")
    parser.add_argument("--domain", action="store", required=True,
                        help="domain name to compile")
    parser.add_argument("--compress_output", action="store_true",
                        help="compress the generated profiles")
    parser.add_argument("--xml_output", action="store_true",
                        help="generate XML profiles")
    parser.add_argument("--no_xml_output", dest="xml_output",
                        action="store_false",
                        help="suppress XML profiles")
    parser.add_argument("--json_output", action="store_true",
                        help="generate JSON profiles")
    parser.add_argument("--no_json_output", dest="json_output",
                        action="store_false",
                        help="suppress JSON profiles")
    parser.add_argument("--panc_jar", action="store",
                        help="location of panc.jar")
    parser.add_argument("--templates", action="store", required=True,
                        help="location of the domain templates")
    parser.add_argument("--swrep", action="store",
                        help="location of the swrep templates")
    parser.add_argument("--batch_size", action="store", type=int,
                        help="compiler batch size")

    options = parser.parse_args()
    config = Config(configfile=options.config)

    return run_domain_compile(options, config)


if __name__ == "__main__":
    raise SystemExit(main())
