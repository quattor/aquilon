#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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

import sys
import os
import subprocess

class DocProcessor(object):
    """generate html, pdf, and epub from markdown sources"""

    commands = {'html': ['pandoc',
                         '--write=html5', '--css=css/screen.css',
                         '--standalone', '--toc', '--number-sections', 
                         '-o %s', 'title.txt'],
                'epub': ['pandoc',
                         '--write=epub', 
                         '--standalone', '--toc', '--number-sections', 
                         '-o %s', 'title.txt'],
                'pdf': ['pandoc',
                        '--standalone', '--toc', '--number-sections', 
                        '--include-in-header=pdf-header-includes.txt',
                        '--variable=geometry:a4paper',
                        '--variable=fontsize:12pt',
                        '--variable=documentclass:book',
                        '--variable=graphics:1',
                        '--listings', 
                        '-o %s', 'title.txt']}

    def get_markdown_sources(self):
        markdown_sources = []
        for file in os.listdir('.'):
            if file.endswith('.md'):
                markdown_sources.append(file)
        markdown_sources.sort()
        return markdown_sources

    def set_filenames(self):
        self.filenames = {}
        for ext in DocProcessor.commands.keys():
            path = os.path.join(self.output_path, self.output_name + '.' + ext)
            self.filenames[ext] = path

    def __init__(self, args):
        if len(args) != 3:
            raise Exception('arguments are: output_path and output_name')

        self.output_path = args[1]
        self.output_name = args[2]

        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        if not os.path.isdir(self.output_path):
            raise Exception('output_path is not a directory' % self.output_path)

        if not len(self.output_name):
            raise Exception('output_name cannot be empty')

        self.set_filenames()

    def exec_cmd(self, full_cmd):
        p = subprocess.Popen(full_cmd, shell=True, 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.STDOUT)
        cmd_output = p.stdout.readlines()
        retval = p.wait()
        if retval != 0:
            raise Exception("error running command:\n%s\noutput:\n%s\n" % \
                                (full_cmd, "\n".join(cmd_output)))

    def run(self):
        srcs = ' '.join(self.get_markdown_sources())
        for ext in DocProcessor.commands.keys():
            filename = self.filenames[ext]
            cmd = ' '.join(DocProcessor.commands[ext]) % filename
            self.exec_cmd('%s %s' % (cmd, srcs))

if __name__ == '__main__':
    # arguments must be output path and output name
    processor = DocProcessor(sys.argv)
    processor.run()
