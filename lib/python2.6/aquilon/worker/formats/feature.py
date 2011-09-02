# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
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
"""Feature formatter."""

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import (Feature, HostFeature, HardwareFeature,
                                InterfaceFeature)


class FeatureFormatter(ObjectFormatter):

    def format_raw(self, feature, indent=""):
        details = []
        details.append(indent + "{0:c}: {0.name}".format(feature))
        if feature.post_call_allowed:
            details.append(indent + "  Post Call: %s" % feature.post_call)
        details.append(indent + "  Template: %s" % feature.cfg_path)

        for link in feature.links:
            opts = []
            if link.model:
                opts.append(format(link.model))
            if link.archetype:
                opts.append(format(link.archetype))
            if link.personality:
                opts.append(format(link.personality))
            if link.interface_name:
                opts.append("Interface %s" % link.interface_name)

            details.append(indent + "  Bound to: %s" % ", ".join(opts))

        if feature.comments:
            details.append(indent + "  Comments: %s" % feature.comments)

        return "\n".join(details)

ObjectFormatter.handlers[Feature] = FeatureFormatter()
ObjectFormatter.handlers[HostFeature] = FeatureFormatter()
ObjectFormatter.handlers[HardwareFeature] = FeatureFormatter()
ObjectFormatter.handlers[InterfaceFeature] = FeatureFormatter()
