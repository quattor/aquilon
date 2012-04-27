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

from aquilon.worker.templates.base import Plenary
from aquilon.worker.templates.panutils import pan, StructureTemplate
from aquilon.worker.locks import CompileKey
from aquilon.aqdb.model import MetaCluster


LOGGER = logging.getLogger(__name__)


class PlenaryMetaCluster(Plenary):
    """
    TODO
    """

    template_type = "object"

    def __init__(self, dbmetacluster, logger=LOGGER):
        Plenary.__init__(self, dbmetacluster, logger=logger)
        self.dbobj = dbmetacluster
        self.name = dbmetacluster.name

        self.plenary_core = "clusters"
        self.plenary_template = dbmetacluster.name

    def get_key(self):
        return CompileKey(domain=self.dbobj.branch.name,
                          profile=self.plenary_template, logger=self.logger)

    def body(self, lines):
        arcdir = self.dbobj.personality.archetype.name
        lines.append("# this is an %s metacluster, so all templates "
                     "should be sourced from there" % arcdir)
        lines.append("variable LOADPATH = %s;" % pan([arcdir]))
        lines.append("")

        lines.append("include { 'pan/units' };")
        lines.append("include { 'pan/functions' };")
        lines.append("")
        lines.append('"/system/metacluster/name" = %s;' % pan(self.name))
        lines.append('"/system/metacluster/type" = %s;' %
                        pan(self.dbobj.cluster_type))

        dbloc = self.dbobj.location_constraint
        lines.append('"/system/metacluster/sysloc/location" = %s;' %
                     pan(dbloc.sysloc()))
        if dbloc.continent:
            lines.append('"/system/metacluster/sysloc/continent" = %s;' %
                         pan(dbloc.continent.name))
        if dbloc.city:
            lines.append('"/system/metacluster/sysloc/city" = %s;' %
                         pan(dbloc.city.name))
        if dbloc.campus:
            lines.append('"/system/metacluster/sysloc/campus" = %s;' %
                         pan(dbloc.campus.name))
            ## maintaining this so templates dont break
            ## during transtion period.. should be DEPRECATED
            lines.append('"/system/metacluster/campus" = %s;' %
                         pan(dbloc.campus.name))
        if dbloc.building:
            lines.append('"/system/metacluster/sysloc/building" = %s;' %
                         pan(dbloc.building.name))
        if dbloc.rack:
            lines.append('"/system/metacluster/rack/row" = %s;' %
                         pan(dbloc.rack.rack_row))
            lines.append('"/system/metacluster/rack/column" = %s;' %
                         pan(dbloc.rack.rack_column))
            lines.append('"/system/metacluster/rack/name" = %s;' %
                         pan(dbloc.rack.name))

        lines.append("")

        lines.append('"/system/metacluster/members" = %s;' %
                     pan([member.name for member in self.dbobj.members]))

        lines.append("")

        lines.append('"/system/build" = %s;' % pan(self.dbobj.status.name))

        lines.append("")
        lines.append('"/metadata/template/branch/name" = %s;' %
                     pan(self.dbobj.branch.name))
        lines.append('"/metadata/template/branch/type" = %s;' %
                     pan(self.dbobj.branch.branch_type))
        if self.dbobj.branch.branch_type == 'sandbox':
            lines.append('"/metadata/template/branch/author" = %s;' %
                         pan(self.dbobj.sandbox_author.name))

        lines.append("include { 'archetype/base' };")

        lines.append("")
        for resource in sorted(self.dbobj.resources):
            lines.append("'/system/resources/%s' = push(%s);" % (
                         resource.resource_type,
                         pan(StructureTemplate(resource.template_base +
                                               '/config'))))

        #for esx_management_server
        for servinst in sorted(self.dbobj.service_bindings):
            lines.append("include { 'service/%s/%s/client/config' };" % \
                         (servinst.service.name, servinst.name))

        lines.append("")
        lines.append("include { 'personality/%s/config' };" %
                     self.dbobj.personality.name)
        lines.append("")
        lines.append("include { 'archetype/final' };")


Plenary.handlers[MetaCluster] = PlenaryMetaCluster

