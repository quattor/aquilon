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

class PlenaryService(Plenary):
    def __init__(self, dbservice):
        Plenary.__init__(self)
        self.name = dbservice.name
        self.plenary_core = "servicedata/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/config" % self.__dict__

    def body(self, lines):
        return


class PlenaryServiceInstance(Plenary):
    def __init__(self, dbservice, dbinstance):
        Plenary.__init__(self)
        self.servers = dbinstance.servers
        self.service = dbservice.name
        self.name = dbinstance.name
        self.plenary_core = "servicedata/%(service)s/%(name)s" % self.__dict__
        self.plenary_template = self.plenary_core + "/config"
        self.template_type = 'structure'

    def body(self, lines):
        lines.append("include { 'servicedata/%(service)s/config' };" % self.__dict__)
        lines.append("");
        lines.append("'instance' = '%(name)s';" % self.__dict__)
        lines.append("'servers' = list(" + ", ".join([("'" + sis.system.fqdn + "'") for sis in self.servers]) + ");")


class PlenaryServiceInstanceClientDefault(Plenary):
    def __init__(self, dbservice, dbinstance):
        Plenary.__init__(self)
        self.servers = dbinstance.servers
        self.service = dbservice.name
        self.name = dbinstance.name
        self.plenary_core = "service/%(service)s/%(name)s/client" % self.__dict__
        self.plenary_template = self.plenary_core + "/config"
        self.template_type = ''

    def body(self, lines):
        lines.append("'/system/services/%(service)s' = create('servicedata/%(service)s/%(name)s/config');" % self.__dict__)

