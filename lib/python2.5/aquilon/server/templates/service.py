# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
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


class PlenaryServiceClientDefault(Plenary):
    def __init__(self, dbservice):
        Plenary.__init__(self)
        self.name = dbservice.name
        self.plenary_core = "service/%(name)s/client" % self.__dict__
        self.plenary_template = "%(plenary_core)s/config" % self.__dict__
        self.template_type = ''

    def body(self, lines):
        return

class PlenaryServiceServerDefault(Plenary):
    def __init__(self, dbservice):
        Plenary.__init__(self)
        self.name = dbservice.name
        self.plenary_core = "service/%(name)s/server" % self.__dict__
        self.plenary_template = "%(plenary_core)s/config" % self.__dict__
        self.template_type = ''

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

class PlenaryServiceInstanceServer(Plenary):
    def __init__(self, dbservice, dbinstance):
        Plenary.__init__(self)
        self.servers = dbinstance.servers
        self.service = dbservice.name
        self.path    = dbinstance.cfg_path
        self.name = dbinstance.name
        self.plenary_core = "servicedata/%(service)s/%(name)s" % self.__dict__
        self.plenary_template = self.plenary_core + "/srvconfig"
        self.template_type = 'structure'

    def body(self, lines):
        lines.append("'instance' = '%(name)s';" % self.__dict__)
        lines.append("'clients' = list(" + ", ".join([("'" + client.host.fqdn + "'") for client in self.path.build_items]) + ");")


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
        lines.append("include { 'service/%(service)s/client/config' };"%self.__dict__)

class PlenaryServiceInstanceServerDefault(Plenary):
    def __init__(self, dbservice, dbinstance):
        Plenary.__init__(self)
        self.servers = dbinstance.servers
        self.service = dbservice.name
        self.name = dbinstance.name
        self.plenary_core = "service/%(service)s/%(name)s/server" % self.__dict__
        self.plenary_template = self.plenary_core + "/config"
        self.template_type = ''

    def body(self, lines):
        lines.append("'/system/provides/%(service)s' = create('servicedata/%(service)s/%(name)s/srvconfig');" % self.__dict__)
        lines.append("include { 'service/%(service)s/server/config' };"%self.__dict__)

