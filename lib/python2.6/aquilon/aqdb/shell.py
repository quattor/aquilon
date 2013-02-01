#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
import sys

_DIR = os.path.dirname(os.path.realpath(__file__))
_LIBDIR = os.path.join(_DIR, '..', '..')
if _LIBDIR not in sys.path:
    sys.path.insert(0, _LIBDIR)

import aquilon.aqdb.depends  # pylint: disable=W0611

import argparse

from ipaddr import IPv4Address, IPv4Network  # pylint: disable=W0611

import ms.modulecmd

from IPython.config.loader import Config as IPyConfig
from IPython.frontend.terminal.embed import InteractiveShellEmbed

from aquilon.config import Config  # pylint: disable=W0611

# pylint: disable=W0614
from aquilon.aqdb.model import *  # pylint: disable=W0401
from aquilon.aqdb.dsdb import *  # pylint: disable=W0401
from aquilon.aqdb.db_factory import DbFactory

db = DbFactory()
Base.metadata.bind = db.engine
session = s = db.Session()

_banner = '<<<Welcome to the Aquilon shell (courtesy of IPython). Ctrl-D to quit>>>\n'


def main():
    parser = argparse.ArgumentParser(
        description='An ipython shell, useful for testing and exploring aqdb')

    parser.add_argument('-v', action='count', dest='verbose',
                        help='increase verbosity by adding more (-vv), etc.')
    opts = parser.parse_args()

    if opts.verbose >= 1:
        db.engine.echo = True

    if db.engine.url.drivername == 'sqlite':
        prompt = str(db.engine.url).split('///')[1]
    else:
        # couldn't use the underlying dbapi connection.current_schema
        # from the engine as it too is ''
        user = db.engine.url.username or os.environ.get("USER")
        host = db.engine.url.host or 'LOCALHOST'
        prompt = '%s@%s' % (user, host)
        if db.engine.url.database:
            prompt += '/%s'
    prompt += '> '

    ipycfg = IPyConfig()
    ipycfg.PromptManager.in_template = prompt
    ipycfg.PlaintextFormatter.pprint = True
    ipycfg.InteractiveShell.separate_in = ''
    ipycfg.InteractiveShell.separate_out = ''
    ipycfg.InteractiveShell.separate_out2 = ''
    ipycfg.InteractiveShell.colors = 'Linux'
    ipshell = InteractiveShellEmbed(config=ipycfg, banner1=_banner)
    ipshell()


def graph_schema(db=db, file_name="/tmp/aqdb_schema"):
    """ Produces a png image of the schema. """
    import aquilon.aqdb.utils.schema2dot as s2d
    s2d.write_schema_png(db.meta, "%s.png" % file_name)
    s2d.write_schema_dot(db.meta, "%s.dot" % file_name)


if __name__ == '__main__':
    main()
