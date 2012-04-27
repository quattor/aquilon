# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011  Contributor
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


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import MetaCluster

# TODO add extra data based on cluster.py(formats)
class MetaClusterFormatter(ObjectFormatter):
    def format_raw(self, metacluster, indent=""):
        details = [indent + "MetaCluster: %s" % metacluster.name]
        details.append(self.redirect_raw(metacluster.location_constraint,
                                         indent + "  "))
        details.append(indent + "  Max members: %s" % metacluster.max_clusters)
        details.append(indent + "  Max shares: %s" % metacluster.max_shares)
        details.append(indent + "  High availability enabled: %s" %
                       metacluster.high_availability)
        caps = metacluster.get_total_capacity()
        if caps:
            capstr = ", ".join(["%s: %s" % (name, value) for name, value in
                                caps.items()])
        else:
            capstr = None
        details.append(indent + "  Capacity limits: %s" % capstr)
        usage = metacluster.get_total_usage()
        if usage:
            usagestr = ", ".join(["%s: %s" % (name, value) for name, value
                                  in usage.items()])
        else:
            usagestr = None
        details.append(indent + "  Resources used by VMs: %s" % usagestr)
        details.append(self.redirect_raw(metacluster.personality, indent + "  "))
        for cluster in metacluster.members:
            details.append(indent + "  Member: {0}".format(cluster))

        if metacluster.resholder and metacluster.resholder.resources:
            details.append(indent + "  Resources:")
            for resource in metacluster.resholder.resources:
                details.append(self.redirect_raw(resource, indent + "    "))

        # for v1 shares
        for share_name in metacluster.shares:
            details.append(indent + "  Share: %s" % share_name)

        if metacluster.comments:
            details.append(indent + "  Comments: %s" % metacluster.comments)
        return "\n".join(details)

ObjectFormatter.handlers[MetaCluster] = MetaClusterFormatter()
