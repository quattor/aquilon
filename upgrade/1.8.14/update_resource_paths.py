#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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
