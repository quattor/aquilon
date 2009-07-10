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
    """
    The top-level service template does nothing. It is really
    a placeholder which can be overridden by the library
    if so desired. We create a blank skeleton simply to ensure
    that including the top-level template will cause no errors
    when there is no user-supplied override. This template defines
    configuration common to both clients and servers, and is applicable
    to all instances.
    """
    def __init__(self, dbservice):
        Plenary.__init__(self)
        self.name = dbservice.name
        self.plenary_core = "servicedata/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/config" % self.__dict__
        self.dir = self.config.get("broker", "plenarydir")


class PlenaryServiceClientDefault(Plenary):
    """
    Any client of the service should include this
    template eventually. Again, this will typically
    be overridden within the template library and is only
    supplied to ensure correct compilation. This template
    defines configuration for clients only, but is applicable
    to all instances of the service.
    """
    def __init__(self, dbservice):
        Plenary.__init__(self)
        self.name = dbservice.name
        self.plenary_core = "service/%(name)s/client" % self.__dict__
        self.plenary_template = "%(plenary_core)s/config" % self.__dict__
        self.template_type = ''
        self.dir = self.config.get("broker", "plenarydir")


class PlenaryServiceServerDefault(Plenary):
    """
    Any server backing a service instance should include this
    template eventually. Again, this will typically
    be overridden within the template library and is only
    supplied to ensure correct compilation. This template
    defines configuration for servers only, but is applicable
    to all instances of the service.
    """
    def __init__(self, dbservice):
        Plenary.__init__(self)
        self.name = dbservice.name
        self.plenary_core = "service/%(name)s/server" % self.__dict__
        self.plenary_template = "%(plenary_core)s/config" % self.__dict__
        self.template_type = ''
        self.dir = self.config.get("broker", "plenarydir")


class PlenaryServiceInstance(Plenary):
    """
    This structure template provides information for the template
    specific to the service instance and for use by the client.
    This data is separated away from the ServiceInstanceClientDefault
    to allow that template to be overridden in the template library
    while still having access to generated data here (the list of
    servers and the instance name)
    """
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
        lines.append("")
        lines.append("'instance' = '%(name)s';" % self.__dict__)
        lines.append("'servers' = list(" + ", ".join([("'" + sis.system.fqdn + "'") for sis in self.servers]) + ");")

class PlenaryServiceInstanceServer(Plenary):
    """
    This structure template provides information for the template
    specific to the service instance and for use by the server.
    This data is separated away from the ServiceInstanceServerDefault
    to allow that template to be overridden in the template library
    while still having access to the generated data here (the list
    of clients and the instance name)
    """
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
    """
    Any client of the service will include this
    template based on service bindings: it will be directly
    included from within the host.tpl. This may
    be overridden within the template library, but this plenary
    should typically be sufficient without override.
    This template defines configuration for clients only, and
    is specific to the instance.
    """
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
    """
    Any server of the servivce will include this
    template based on service bindings: it will be directly
    included from within the host.tpl. This may be overridden
    within the template library, but this template should be
    sufficient. The template defines configuration for servers
    only and is specific to the service instance.
    """
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

