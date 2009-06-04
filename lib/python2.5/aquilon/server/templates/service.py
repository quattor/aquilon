# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.


from aquilon.server.templates.base import Plenary


class PlenaryService(Plenary):
    def __init__(self, dbservice):
        Plenary.__init__(self)
        self.name = dbservice.name
        self.plenary_core = "servicedata/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/config" % self.__dict__
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        return


class PlenaryServiceClientDefault(Plenary):
    def __init__(self, dbservice):
        Plenary.__init__(self)
        self.name = dbservice.name
        self.plenary_core = "service/%(name)s/client" % self.__dict__
        self.plenary_template = "%(plenary_core)s/config" % self.__dict__
        self.template_type = ''
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        return

class PlenaryServiceServerDefault(Plenary):
    def __init__(self, dbservice):
        Plenary.__init__(self)
        self.name = dbservice.name
        self.plenary_core = "service/%(name)s/server" % self.__dict__
        self.plenary_template = "%(plenary_core)s/config" % self.__dict__
        self.template_type = ''
        self.dir = self.config.get("broker", "plenarydir")

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
        self.dir = self.config.get("broker", "plenarydir")

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
        self.dir = self.config.get("broker", "plenarydir")

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
        self.dir = self.config.get("broker", "plenarydir")

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
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        lines.append("'/system/provides/%(service)s' = create('servicedata/%(service)s/%(name)s/srvconfig');" % self.__dict__)
        lines.append("include { 'service/%(service)s/server/config' };"%self.__dict__)

