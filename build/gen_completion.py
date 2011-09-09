#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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

'''Script generating bash completion code from input.xml.
'''

import ms.version
ms.version.addpkg('Cheetah', '2.4.4')

import os
import sys
import optparse
import xml.etree.ElementTree as ET
from Cheetah.Template import Template

if __name__ == "__main__":
    parser = optparse.OptionParser(usage="usage: %prog [options] template1 [template2 ...]\n   or: %prog [options] --all")
    parser.add_option("-o", "--outputdir", type="string", dest="output_dir",
                      help="the directory to put generated files in", metavar="DIRECTORY")
    parser.add_option("-t", "--templatedir", type="string", dest="template_dir",
                      help="the directory to search for templates", metavar="DIRECTORY")
    parser.add_option("-i", "--input", type="string", dest="input_filename",
                      help="name of the input XML file", metavar="FILE")
    parser.set_defaults(generate_all=False)
    parser.add_option("-a", "--all", action="store_true", dest="generate_all",
                      help="generate output for all available templates")

    bindir = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "..")
    parser.set_defaults(output_dir = ".",
                        template_dir = os.path.join(bindir, "etc", "templates"),
                        input_filename = os.path.join(bindir, "etc", "input.xml"))

    (options, args) = parser.parse_args()

    if options.generate_all:
        if len(args) >= 1:
            parser.print_help()
            sys.exit(os.EX_USAGE)
        for f in os.listdir(options.template_dir):
            if f.endswith('.tmpl'):
                args.append(f[0:-5])

    if len(args) < 1:
        parser.print_help()
        sys.exit(os.EX_USAGE)

    tree = ET.parse( options.input_filename )

    for template_name in args:
        template = Template( file = os.path.join(options.template_dir, template_name + ".tmpl") )
        template.tree = tree

        output_filename = os.path.join(options.output_dir, "aq_" + template_name + "_completion.sh")
        output_file = open(output_filename, "w")
        output_file.write(str(template))
        output_file.close()
