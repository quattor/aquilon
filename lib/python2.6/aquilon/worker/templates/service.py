# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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


import logging

from aquilon.aqdb.model import Service, ServiceInstance
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.templates.panutils import (StructureTemplate, pan_assign,
                                               pan_include)
from aquilon.exceptions_ import NotFoundException

LOGGER = logging.getLogger(__name__)


class PlenaryService(PlenaryCollection):
    """
    A facade for the variety of PlenaryService subsidiary files
    """
    def __init__(self, dbservice, logger=LOGGER):
        PlenaryCollection.__init__(self, logger=logger)
        self.dbobj = dbservice
        self.plenaries.append(PlenaryServiceToplevel(dbservice, logger=logger))
        self.plenaries.append(PlenaryServiceClientDefault(dbservice,
                                                          logger=logger))
        self.plenaries.append(PlenaryServiceServerDefault(dbservice,
                                                          logger=logger))


Plenary.handlers[Service] = PlenaryService


class PlenaryServiceToplevel(Plenary):
    """
    The top-level service template does nothing. It is really
    a placeholder which can be overridden by the library
    if so desired. We create a blank skeleton simply to ensure
    that including the top-level template will cause no errors
    when there is no user-supplied override. This template defines
    configuration common to both clients and servers, and is applicable
    to all instances.
    """

    template_type = "structure"

    def __init__(self, dbservice, logger=LOGGER):
        Plenary.__init__(self, dbservice, logger=logger)
        self.plenary_core = "servicedata/%s" % dbservice.name
        self.plenary_template = "config"


class PlenaryServiceClientDefault(Plenary):
    """
    Any client of the service should include this
    template eventually. Again, this will typically
    be overridden within the template library and is only
    supplied to ensure correct compilation. This template
    defines configuration for clients only, but is applicable
    to all instances of the service.
    """

    template_type = ""

    def __init__(self, dbservice, logger=LOGGER):
        Plenary.__init__(self, dbservice, logger=logger)
        self.plenary_core = "service/%s/client" % dbservice.name
        self.plenary_template = "config"


class PlenaryServiceServerDefault(Plenary):
    """
    Any server backing a service instance should include this
    template eventually. Again, this will typically
    be overridden within the template library and is only
    supplied to ensure correct compilation. This template
    defines configuration for servers only, but is applicable
    to all instances of the service.
    """

    template_type = ""

    def __init__(self, dbservice, logger=LOGGER):
        Plenary.__init__(self, dbservice, logger=logger)
        self.plenary_core = "service/%s/server" % dbservice.name
        self.plenary_template = "config"


class PlenaryServiceInstance(PlenaryCollection):
    """
    A facade for the variety of PlenaryServiceInstance subsidiary files
    """
    def __init__(self, dbinstance, logger=LOGGER):
        PlenaryCollection.__init__(self, logger=logger)
        self.plenaries.append(PlenaryServiceInstanceToplevel(dbinstance,
                                                             logger=logger))
        self.plenaries.append(PlenaryServiceInstanceClientDefault(dbinstance,
                                                                  logger=logger))
        self.plenaries.append(PlenaryServiceInstanceServer(dbinstance,
                                                           logger=logger))
        self.plenaries.append(PlenaryServiceInstanceServerDefault(dbinstance,
                                                                  logger=logger))


Plenary.handlers[ServiceInstance] = PlenaryServiceInstance


class PlenaryServiceInstanceToplevel(Plenary):
    """
    This structure template provides information for the template
    specific to the service instance and for use by the client.
    This data is separated away from the ServiceInstanceClientDefault
    to allow that template to be overridden in the template library
    while still having access to generated data here (the list of
    servers and the instance name)
    """

    template_type = "structure"

    def __init__(self, dbinstance, logger=LOGGER):
        Plenary.__init__(self, dbinstance, logger=logger)
        self.service = dbinstance.service.name
        self.name = dbinstance.name
        self.plenary_core = "servicedata/%(service)s/%(name)s" % self.__dict__
        self.plenary_template = "config"

    def body(self, lines):
        pan_include(lines, "servicedata/%s/config" % self.service)
        lines.append("")
        pan_assign(lines, "instance", self.name)
        pan_assign(lines, "servers", self.dbobj.server_fqdns)
        if self.service == 'dns':
            pan_assign(lines, "server_ips", self.dbobj.server_ips)


class PlenaryServiceInstanceServer(Plenary):
    """
    This structure template provides information for the template
    specific to the service instance and for use by the server.
    This data is separated away from the PlenaryServiceInstanceServerDefault
    to allow that template to be overridden in the template library
    while still having access to the generated data here (the list
    of clients and the instance name)
    """

    template_type = "structure"

    def __init__(self, dbinstance, logger=LOGGER):
        Plenary.__init__(self, dbinstance, logger=logger)
        self.service = dbinstance.service.name
        self.name = dbinstance.name
        self.plenary_core = "servicedata/%(service)s/%(name)s" % self.__dict__
        self.plenary_template = "srvconfig"

    def body(self, lines):
        pan_assign(lines, "instance", self.name)
        pan_assign(lines, "clients", self.dbobj.client_fqdns)


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

    template_type = ""

    def __init__(self, dbinstance, logger=LOGGER):
        Plenary.__init__(self, dbinstance, logger=logger)
        self.service = dbinstance.service.name
        self.name = dbinstance.name
        self.plenary_core = "service/%(service)s/%(name)s/client" % self.__dict__
        self.plenary_template = "config"

    def body(self, lines):
        pan_assign(lines, "/system/services/%s" % self.service,
                   StructureTemplate('servicedata/%s/%s/config' % (self.service,
                                                                   self.name)))
        pan_include(lines, "service/%s/client/config" % self.service)


class PlenaryServiceInstanceServerDefault(Plenary):
    """
    Any server of the servivce will include this
    template based on service bindings: it will be directly
    included from within the host.tpl. This may be overridden
    within the template library, but this template should be
    sufficient. The template defines configuration for servers
    only and is specific to the service instance.
    """

    template_type = ""

    def __init__(self, dbinstance, logger=LOGGER):
        Plenary.__init__(self, dbinstance, logger=logger)
        self.service = dbinstance.service.name
        self.name = dbinstance.name
        self.plenary_core = "service/%(service)s/%(name)s/server" % self.__dict__
        self.plenary_template = "config"

    def body(self, lines):
        pan_assign(lines, "/system/provides/%s" % self.service,
                   StructureTemplate('servicedata/%s/%s/srvconfig' %
                                     (self.service, self.name)))
        pan_include(lines, "service/%s/server/config" % self.service)
