#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley

'''Script generating bash completion code from input.xml.
'''

import msversion
msversion.addpkg('Cheetah', '2.0.1-py25', 'dist')

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

    bindir = os.path.dirname( os.path.realpath(sys.argv[0]) )
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
