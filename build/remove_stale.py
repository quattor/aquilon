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
""" Remove any old entries in the install tree, used by Makefile."""

import os
import sys


def clean_old(installdir):
    if not os.path.isdir(installdir):
        print >>sys.stderr, "Warning: '%s' is not a directory, not searching " \
                "for and removing stale files." % installdir
        return
    src = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
    for (dirpath, dirnames, filenames) in os.walk(installdir):
        relative_dirpath = dirpath.replace(installdir, '', 1)
        for f in filenames:
            # Can't compare with src, since we only have .py files there.
            # Assume that the .pyc will either be removed because its
            # corresponding .py is removed, or rebuilt as necessary.
            if f.endswith('.pyc'):
                continue
            # This will be updated as needed, and has no corresponding
            # file in src.
            if f == 'dropin.cache':
                continue
            if not os.path.exists(os.path.join(src, relative_dirpath, f)):
                old_file = os.path.join(dirpath, f)
                print "Removing %s" % old_file
                os.remove(old_file)
                if old_file.endswith('.py'):
                    old_pyc = old_file + 'c'
                    if os.path.exists(old_pyc):
                        print "Removing %s" % old_pyc
                        os.remove(old_pyc)


if __name__ == '__main__':
    if len(sys.argv) > 2:
        print >>sys.stderr, "Takes only one argument, the install directory to prune."
        sys.exit(1)
    if len(sys.argv) < 2:
        print >>sys.stderr, "The install directory to prune is required."
        sys.exit(1)
    clean_old(sys.argv[1])
