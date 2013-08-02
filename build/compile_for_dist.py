#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013  Contributor
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
"""Add /ms/dist to traceback of files compiled in /ms/dev."""


import sys
import py_compile
import re


def main(args=None):
    """Except for the custom dfile, this is stolen directly from py_compile.

    Compile all of the given filename arguments.  This custom version
    replaces /ms/dev in the path with /ms/dist to match our environment usage.

    """
    if args is None:
        args = sys.argv[1:]
    dev_re = re.compile(r'/ms/dev/(?P<meta>[^/]+)/(?P<proj>[^/]+)'
                        r'/(?P<release>[^/]+)/install/(?P<path>.*)')
    for filename in args:
        try:
            m = dev_re.match(filename)
            if m:
                dfile = "/ms/dist/%(meta)s/PROJ/%(proj)s" \
                        "/%(release)s/%(path)s" % m.groupdict()
            else:
                dfile = filename
            py_compile.compile(filename, dfile=dfile, doraise=True)
        except py_compile.PyCompileError, e:
            sys.stderr.write(e.msg)


if __name__ == "__main__":
    main()
