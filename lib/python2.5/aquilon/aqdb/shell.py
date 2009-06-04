#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
import optparse
import tempfile

import subprocess as sp

_DIR    = os.path.dirname(os.path.realpath(__file__))
_LIBDIR = os.path.join(_DIR, '..','..')
_TESTDIR=os.path.join(_DIR,'..','..','..','..','tests','aqdb')

if _LIBDIR not in sys.path:
    sys.path.insert(0,_LIBDIR)

if _TESTDIR not in sys.path:
    sys.path.insert(1,_TESTDIR)

import aquilon.aqdb.depends

#FOR ALL YOU HATERS: this IS for interactive work. Step off the import * ;)
from aquilon.aqdb.model      import *
from aquilon.aqdb.dsdb       import *
from aquilon.aqdb.db_factory import db_factory
from aquilon.aqdb.utils      import schema2dot


from IPython.Shell import IPShellEmbed
_banner  = '***Embedded IPython, Ctrl-D to quit.'
_args    = []
ipshell = IPShellEmbed(_args, banner=_banner)

def configure(*args, **kw):
    usage = """ usage: %prog [options] """

    desc = 'An ipython shell, useful for testing and exploring'

    p = optparse.OptionParser(usage=usage, prog=sys.argv[0], version='0.1',
                              description=desc)

    p.add_option('-v',
                 action = 'count',
                 dest   = 'verbose',
                 help   = 'increase verbosity by adding more (vv), etc.')

    opts, args = p.parse_args()
    return opts

def main(*args, **kw):
    opts = configure(*args, **kw)

    db = db_factory()
    Base.metadata.bind = db.engine
    s = db.Session()

    #left a hole in between for verbose=1. not sure we'll ever use it
    if opts.verbose > 2:
        Base.metadata.bind.echo = True

    ipshell()

#TODO: schema/uml as an argument (DRY)
def graph_schema(db, file_name="/tmp/aqdb_schema.png"):
    schema2dot.write_schema_graph(db,file_name)

if __name__ == '__main__':
    main(sys.argv)
