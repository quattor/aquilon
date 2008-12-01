# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""CfgPath formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.cfg.cfg_path import CfgPath


class CfgPathFormatter(ObjectFormatter):
    def format_raw(self, cfg_path, indent=""):
        return indent + "Template: %s" % cfg_path

ObjectFormatter.handlers[CfgPath] = CfgPathFormatter()


