# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""UserPrincipal formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import UserPrincipal


class UserPrincipalFormatter(ObjectFormatter):
    def format_raw(self, user_principal, indent=""):
        details = [indent + "UserPrincipal: %s [role: %s]" %
                (user_principal, user_principal.role.name)]
        if user_principal.comments:
            details.append(indent + "  Comments: %s" % user_principal.comments)
        return "\n".join(details)

ObjectFormatter.handlers[UserPrincipal] = UserPrincipalFormatter()


