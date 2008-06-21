#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Model formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.hardware import Model


class ModelFormatter(ObjectFormatter):
    def format_raw(self, model, indent=""):
        details = [indent + "Model: %s %s" % (model.vendor.name, model.name)]
        if model.comments:
            details.append(indent + "  Comments: %s" % model.comments)
        if model.specifications:
            details.append(self.redirect_raw(model.specifications, indent+"  "))
        return "\n".join(details)

ObjectFormatter.handlers[Model] = ModelFormatter()


#if __name__=='__main__':
