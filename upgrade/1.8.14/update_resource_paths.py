#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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
"""
Reconfigure hosts affected by the resource path changes
"""

import os, os.path
import sys
import logging

BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(os.path.join(BINDIR, "..", "..", "lib", "python2.6"))

import aquilon.aqdb.depends
import aquilon.worker.depends
from aquilon.config import Config

from aquilon.exceptions_ import AquilonError, IncompleteError
from aquilon.aqdb.model import Base, Resource, ResourceGroup, Cluster, Host
from aquilon.aqdb.db_factory import DbFactory
from aquilon.worker.templates.base import PlenaryCollection
from aquilon.worker.templates.resource import PlenaryResource
from aquilon.worker.templates.cluster import PlenaryCluster
from aquilon.worker.templates.host import PlenaryHost
from aquilon.worker.locks import CompileKey

db = DbFactory()
Base.metadata.bind = db.engine

session = db.Session()
config = Config()

def main():
    logging.basicConfig(level=logging.DEBUG)

    query = session.query(Resource)

    old_paths = []

    with CompileKey():
        for res in query.all():
            PlenaryResource(res).write(locked=True)

            holder = res.holder.holder_object
            if isinstance(holder, ResourceGroup):
                holder = holder.holder.holder_object
            else:
                old_paths.append("resource/%s/%s/%s/%s" % (res.resource_type,
                                                           res.holder.holder_type,
                                                           res.holder.holder_name,
                                                           res.name))

            try:
                # Show that something is happening...
                print "Flushing {0:l}".format(holder)

                if isinstance(holder, Host):
                    PlenaryHost(holder).write(locked=True)
                elif isinstance(holder, Cluster):
                    PlenaryCluster(holder).write(locked=True)
                else:
                    raise AquilonError("Unknown holder object: %r" % holder)
            except IncompleteError:
                pass

    plenarydir = config.get("broker", "plenarydir")
    for path in old_paths:
        try:
            os.remove(os.path.join(plenarydir, path, "config.tpl"))
        except OSError:
            pass
        try:
            os.removedirs(os.path.join(plenarydir, path))
        except OSError:
            pass


if __name__ == '__main__':
    main()
