# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# See LICENSE for copying information
#
# This module is part of Aquilon


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import Vendor

class VendorFormatter(ObjectFormatter):
    def format_raw(self, vendor, indent=""):
        details = [ indent + "Vendor: %s" % vendor.name ]
        if vendor.comments:
            details.append(indent + "  Comments: %s" % vendor.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Vendor] = VendorFormatter()


