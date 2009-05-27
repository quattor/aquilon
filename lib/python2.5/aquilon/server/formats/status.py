# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Status formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import Status


class StatusFormatter(ObjectFormatter):
    def format_raw(self, status, indent=""):
        details = [ indent + "Build Status: %s" % status.name ]
        if status.comments:
            details.append(indent + "  Comments: %s" % status.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Status] = StatusFormatter()


