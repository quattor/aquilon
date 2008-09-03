#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon

from aquilon.server.templates.base import Plenary

class PlenaryPersonality(Plenary):
    def __init__(self, dbpersona):
        Plenary.__init__(self)
        self.name = dbpersona.relative_path
        self.plenary_core = "personality/%(name)s" % self.__dict__
        self.plenary_template = self.plenary_core + "/config"
        self.template_type = ''

    def body(self, lines):
        return

