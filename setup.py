#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013,2014  Contributor
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
"""Basic setup.py for packaging Aquilon itself"""

import glob
import os
import shutil
import sys
from distutils.core import setup
from subprocess import Popen, PIPE
from distutils.command.install_scripts import install_scripts
from distutils.command.build import build

VERSIONFILE = "VERSION"

# distutils won't package anything under "build".  We cheat by
# creating a symlink and referring to it during all the packaging
# process.
try:
    os.symlink("build", "bootstrap")
except OSError:
    pass

class BuildExcept(Exception):
    pass


def get_version():
    """Returns a version for the package, based on git-describe, or in the
    VERSION file."""
    try:
        with open(VERSIONFILE) as f:
            return f.readline().strip()
    except IOError:
        with open(VERSIONFILE, "w") as f:
            p = Popen("git describe".split(), stdout=f)
            if p.wait() == 0:
                return get_version()
            else:
                raise


def find_packages(path):
    """Finds all the Python packages under path"""
    n = len(path)+1
    l = []
    for dirpath, dirnames, filenames in os.walk(path):
        for d in dirnames:
            base = dirpath[n:].replace(os.path.sep, ".")
            base = base.strip()
            if base:
                m = '.'.join([base, d])
            else:
                m = d
            l.append(m)
    return l

def find_regular_files(path):
    """Finds all the regular files under a directory and returns the
    tuples that would install such files"""
    l = []
    for dirpath, dirnames, filenames in os.walk(path):
        base = dirpath.strip()
        if base and filenames:
            l.append(("/usr/share/aquilon/%s" % base,
                      [os.path.join(base, f) for f in filenames
                       if not f.endswith("py")]))
    return l


all_packages = find_packages("lib")
all_packages.extend(find_packages("bootstrap/bootstrap_ms"))
all_scripts = glob.glob(os.path.join("bin", "a*")) + \
              glob.glob(os.path.join("sbin", "a*"))
all_scripts.extend(glob.glob(os.path.join("bootstrap", "*.py")))

setup(name="aquilon",
      version=get_version(),
      description="Aquilon",
      long_description="""Aquilon looks cool""",
      license="Apache 2.0",
      author="Quattor collaboration",
      author_email="quattor-aquilon@lists.sourceforge.net",
      package_dir={'aquilon' : 'lib/aquilon',
                   'twisted' : 'lib/twisted',
                   'ms': 'bootstrap/bootstrap_ms/ms'},
      packages=all_packages,
      cmdclass = {"install_scripts" : install_scripts},
      data_files=[("/usr/share/aquilon/etc",
                   glob.glob("etc/*.conf*") + glob.glob("etc/*xml")),
                  ("/etc/init.d", ["etc/rc.d/init.d/aqd"]),
                  ("/etc/sysconfig", ["etc/sysconfig/aqd"]),
                  ("/etc/bash_completion.d", ["aq_bash_completion.sh"]),
                  ("/usr/share/aquilon/mako/raw", glob.glob("etc/mako/raw/*")),
                  ("/usr/share/aquilon/mako/pan", glob.glob("etc/mako/pan/*")),
                  ("/usr/share/aquilon/mako/html", glob.glob("etc/mako/html/*")),
                  ("/usr/share/man/man1", glob.glob("doc/man/man1/*gz"))
                  ] + find_regular_files("upgrade"),
      scripts=all_scripts,
      url="http://quattor.org")
