#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
""" Remove any old entries in the install tree, used by Makefile."""

import os
import sys

def clean_old(installdir):
    if not os.path.isdir(installdir):
        print >>sys.stderr, "Warning: '%s' is not a directory, not searching for and removing stale files." % installdir
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

