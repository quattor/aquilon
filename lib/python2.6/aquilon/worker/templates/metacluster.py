# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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


import logging

from aquilon.aqdb.model import MetaCluster
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.templates.panutils import (StructureTemplate, pan_assign,
                                               pan_include, pan_push,
                                               pan_variable)
from aquilon.worker.locks import CompileKey


LOGGER = logging.getLogger(__name__)


class PlenaryMetaCluster(PlenaryCollection):
    """
    A facade for the variety of PlenaryMetaCluster subsidiary files
    """
    def __init__(self, dbcluster, logger=LOGGER):
        PlenaryCollection.__init__(self, logger=LOGGER)
        self.dbobj = dbcluster
        self.plenaries.append(PlenaryMetaClusterObject(dbcluster, logger=logger))
        self.plenaries.append(PlenaryMetaClusterData(dbcluster, logger=logger))

class PlenaryMetaClusterData(Plenary):
    """
    TODO
    """

    template_type = ""

    def __init__(self, dbmetacluster, logger=LOGGER):
        Plenary.__init__(self, dbmetacluster, logger=logger)
        self.name = dbmetacluster.name

        # TODO maybe metaclusterdata
        self.plenary_core = "clusterdata"
        self.plenary_template = dbmetacluster.name

    def get_key(self):
        return CompileKey(domain=self.dbobj.branch.name,
                          profile=self.plenary_template, logger=self.logger)

    def body(self, lines):
        pan_include(lines, ["pan/units", "pan/functions"])
        lines.append("")
        pan_assign(lines, "/system/metacluster/name", self.name)
        pan_assign(lines, "/system/metacluster/type", self.dbobj.cluster_type)

        dbloc = self.dbobj.location_constraint
        pan_assign(lines, "/system/metacluster/sysloc/location", dbloc.sysloc())
        if dbloc.continent:
            pan_assign(lines, "/system/metacluster/sysloc/continent",
                       dbloc.continent.name)
        if dbloc.city:
            pan_assign(lines, "/system/metacluster/sysloc/city", dbloc.city.name)
        if dbloc.campus:
            pan_assign(lines, "/system/metacluster/sysloc/campus",
                       dbloc.campus.name)
            ## maintaining this so templates dont break
            ## during transtion period.. should be DEPRECATED
            pan_assign(lines, "/system/metacluster/campus", dbloc.campus.name)
        if dbloc.building:
            pan_assign(lines, "/system/metacluster/sysloc/building",
                       dbloc.building.name)
        if dbloc.rack:
            pan_assign(lines, "/system/metacluster/rack/row",
                       dbloc.rack.rack_row)
            pan_assign(lines, "/system/metacluster/rack/column",
                       dbloc.rack.rack_column)
            pan_assign(lines, "/system/metacluster/rack/name",
                       dbloc.rack.name)

        lines.append("")

        pan_assign(lines, "/system/metacluster/members",
                   [member.name for member in self.dbobj.members])

        lines.append("")

        pan_assign(lines, "/system/build", self.dbobj.status.name)

        lines.append("")
        if self.dbobj.resholder:
            for resource in sorted(self.dbobj.resholder.resources):
                pan_push(lines, "/system/resources/%s" % resource.resource_type,
                         StructureTemplate(resource.template_base + '/config'))

class PlenaryMetaClusterObject(Plenary):
    """
    TODO
    """

    template_type = "object"

    def __init__(self, dbmetacluster, logger=LOGGER):
        Plenary.__init__(self, dbmetacluster, logger=logger)
        self.name = dbmetacluster.name

        self.loadpath = self.dbobj.personality.archetype.name
        self.plenary_core = "clusters"
        self.plenary_template = dbmetacluster.name

    def get_key(self):
        return CompileKey(domain=self.dbobj.branch.name,
                          profile=self.plenary_template, logger=self.logger)

    def body(self, lines):
        pan_include(lines, ["pan/units", "pan/functions"])
        pan_include(lines, "clusterdata/%s" % self.name)
        pan_include(lines, "archetype/base")

        #for esx_management_server
        for servinst in sorted(self.dbobj.service_bindings):
            pan_include(lines, "service/%s/%s/client/config" %
                        (servinst.service.name, servinst.name))

        pan_include(lines, "personality/%s/config" %
                    self.dbobj.personality.name)
        pan_include(lines, "archetype/final")


Plenary.handlers[MetaCluster] = PlenaryMetaCluster

