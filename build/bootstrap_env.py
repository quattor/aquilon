#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011  Contributor
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
import os
import virtualenv
import textwrap
import re


def gather_deps(dir):
    depfiles = []
    for (dirpath, dirnames, filenames) in os.walk(dir):
        if 'depends.py' in filenames:
            depfiles.append(os.path.join(dirpath, 'depends.py'))
    dependencies = {}
    dep_re = re.compile(r"^\s*ms.version.addpkg\(\s*'(.*?)'\s*,\s*'(.*?)(-ms\d+)?'")
    for depfile in depfiles:
        with open(depfile) as f:
            for line in f.readlines():
                m = dep_re.search(line)
                if m:
                    (package, version, _) = m.groups()
                    if package.startswith('ms.'):
                        continue
                    if package in ['setuptools']:
                        continue
                    dependencies[package] = version
    return dependencies


def bootstrap(dependencies, dir):
    extra = textwrap.dedent("""
    import os, subprocess
    import urllib
    from tempfile import mkdtemp
    def extend_parser(optparse_parser):
        pass
    def adjust_options(options, args):
        pass
    def after_install(options, home_dir):
        easy_install = join(home_dir, 'bin', 'easy_install')
    """)
    for package in sorted(dependencies.keys()):
        if package == 'protobuf':
            continue
        extra += "    if subprocess.call([easy_install, '%s==%s']) != 0:\n" % (
            package, dependencies[package])
        extra += "        subprocess.call([easy_install, '%s'])\n" % package
    extra += "    subprocess.call([easy_install, '.'], cwd='%s')\n" % (
        os.path.join(dir, 'bootstrap_ms'))
    extra += "    subprocess.call([easy_install, '.'], cwd='%s')\n" % (
        os.path.join(dir, 'bootstrap_Sybase'))
    print virtualenv.create_bootstrap_script(extra)


if __name__ == '__main__':
    dir = os.path.dirname(os.path.realpath(__file__))
    libdir = os.path.join(dir, '..', 'lib', 'python2.6')
    dependencies = gather_deps(libdir)
    print bootstrap(dependencies, dir)
