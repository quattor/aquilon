#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Domain formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.sy.domain import Domain


class DomainFormatter(ObjectFormatter):
    def format_raw(self, domain, indent=""):
        details = [ indent + "Domain: %s" % domain.name ]
        details.append(indent + "  Owner: %s" % domain.owner.name)
        details.append(indent + "  Compiler: %s" % domain.compiler)
        if domain.comments:
            details.append(indent + "  Comments: %s" % domain.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Domain] = DomainFormatter()


#if __name__=='__main__':
