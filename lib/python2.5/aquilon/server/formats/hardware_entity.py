# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""HardwareEntity formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import HardwareEntity


# Should never get invoked...
class HardwareEntityFormatter(ObjectFormatter):
    def format_raw(self, hwe, indent=""):
        details = [indent + "%s: %s" % (hwe.hardware_entity_type,
                                         hwe.hardware_name)]
        details.append(self.redirect_raw(hwe.location, indent + "  "))
        details.append(self.redirect_raw(hwe.model, indent + "  "))
        if hwe.serial_no:
            details.append(indent + "  Serial: %s" % hwe.serial_no)
        for i in hwe.interfaces:
            details.append(self.redirect_raw(i, indent + "  "))
        if hwe.comments:
            details.append(indent + "  Comments: %s" % hwe.comments)
        return "\n".join(details)

ObjectFormatter.handlers[HardwareEntity] = HardwareEntityFormatter()


class SimpleHardwareEntityList(list):
    """By convention, holds a list of systems to be formatted in a simple
       (name-only) manner."""
    pass


class SimpleHardwareEntityListFormatter(ObjectFormatter):
    def format_raw(self, shelist, indent=""):
        return str("\n".join([indent + hw.hardware_name for hw in shelist]))

    # Should probably display some useful info...
    def format_csv(self, shelist):
        return str("\n".join([hw.hardware_name for hw in shelist]))

    # Maybe delegate to each type...?  There is no simple/standard
    # name based hardware search.
    def format_html(self, shelist):
        return self.format_raw(shelist)

ObjectFormatter.handlers[SimpleHardwareEntityList] = \
        SimpleHardwareEntityListFormatter()


