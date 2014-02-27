# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from sqlalchemy.inspection import inspect

from aquilon.aqdb.model import Service, ServiceInstance
from aquilon.worker.locks import NoLockKey, PlenaryKey
from aquilon.worker.templates import (Plenary, StructurePlenary,
                                      PlenaryCollection)
from aquilon.worker.templates.panutils import (StructureTemplate, pan_assign,
                                               pan_include)

LOGGER = logging.getLogger(__name__)


class PlenaryService(PlenaryCollection):
    """
    A facade for the variety of PlenaryService subsidiary files
    """
    def __init__(self, dbservice, logger=LOGGER):
        super(PlenaryService, self).__init__(logger=logger)

        self.dbobj = dbservice
        self.plenaries.append(PlenaryServiceToplevel.get_plenary(dbservice))
        self.plenaries.append(PlenaryServiceClientDefault.get_plenary(dbservice))
        self.plenaries.append(PlenaryServiceServerDefault.get_plenary(dbservice))


Plenary.handlers[Service] = PlenaryService


class PlenaryServiceToplevel(StructurePlenary):
    """
    The top-level service template does nothing. It is really
    a placeholder which can be overridden by the library
    if so desired. We create a blank skeleton simply to ensure
    that including the top-level template will cause no errors
    when there is no user-supplied override. This template defines
    configuration common to both clients and servers, and is applicable
    to all instances.
    """

    prefix = "servicedata"

    @classmethod
    def template_name(cls, dbservice):
        return "%s/%s/config" % (cls.prefix, dbservice.name)


class PlenaryServiceClientDefault(Plenary):
    """
    Any client of the service should include this
    template eventually. Again, this will typically
    be overridden within the template library and is only
    supplied to ensure correct compilation. This template
    defines configuration for clients only, but is applicable
    to all instances of the service.
    """

    prefix = "service"

    @classmethod
    def template_name(cls, dbservice):
        return "%s/%s/client/config" % (cls.prefix, dbservice.name)


class PlenaryServiceServerDefault(Plenary):
    """
    Any server backing a service instance should include this
    template eventually. Again, this will typically
    be overridden within the template library and is only
    supplied to ensure correct compilation. This template
    defines configuration for servers only, but is applicable
    to all instances of the service.
    """

    prefix = "service"

    @classmethod
    def template_name(cls, dbservice):
        return "%s/%s/server/config" % (cls.prefix, dbservice.name)


class SIHelperMixin(object):
    """
    Contains common code for all service instance related plenary classes
    """

    def get_key(self, exclusive=True):
        if inspect(self.dbobj).deleted:
            return NoLockKey(logger=self.logger)
        else:
            return PlenaryKey(service_instance=self.dbobj, logger=self.logger,
                              exclusive=exclusive)

    def __repr__(self):
        # The service instance name is not necessarily unique, so include the
        # name of the service too
        return "%s(%s/%s)" % (self.__class__.__name__, self.dbobj.service.name,
                              self.dbobj.name)


class PlenaryServiceInstance(SIHelperMixin, PlenaryCollection):
    """
    A facade for the variety of PlenaryServiceInstance subsidiary files
    """
    def __init__(self, dbinstance, logger=LOGGER):
        super(PlenaryServiceInstance, self).__init__(logger=logger)
        self.dbobj = dbinstance

        self.plenaries.append(PlenaryServiceInstanceToplevel.get_plenary(dbinstance))
        self.plenaries.append(PlenaryServiceInstanceClientDefault.get_plenary(dbinstance))
        self.plenaries.append(PlenaryServiceInstanceServer.get_plenary(dbinstance))
        self.plenaries.append(PlenaryServiceInstanceServerDefault.get_plenary(dbinstance))

Plenary.handlers[ServiceInstance] = PlenaryServiceInstance


class PlenaryServiceInstanceToplevel(SIHelperMixin, StructurePlenary):
    """
    This structure template provides information for the template
    specific to the service instance and for use by the client.
    This data is separated away from the ServiceInstanceClientDefault
    to allow that template to be overridden in the template library
    while still having access to generated data here (the list of
    servers and the instance name)
    """

    prefix = "servicedata"

    @classmethod
    def template_name(cls, dbinstance):
        return "%s/%s/%s/config" % (cls.prefix, dbinstance.service.name,
                                    dbinstance.name)

    def body(self, lines):
        pan_include(lines,
                    PlenaryServiceToplevel.template_name(self.dbobj.service))
        lines.append("")
        pan_assign(lines, "instance", self.dbobj.name)

        fqdns = [srv.fqdn for srv in self.dbobj.servers]
        ips = [srv.ip for srv in self.dbobj.servers if srv.ip]

        pan_assign(lines, "servers", fqdns)
        pan_assign(lines, "server_ips", ips)


class PlenaryServiceInstanceServer(SIHelperMixin, StructurePlenary):
    """
    This structure template provides information for the template
    specific to the service instance and for use by the server.
    This data is separated away from the PlenaryServiceInstanceServerDefault
    to allow that template to be overridden in the template library
    while still having access to the generated data here (the list
    of clients and the instance name)
    """

    prefix = "servicedata"

    @classmethod
    def template_name(cls, dbinstance):
        return "%s/%s/%s/srvconfig" % (cls.prefix, dbinstance.service.name,
                                       dbinstance.name)

    def body(self, lines):
        pan_assign(lines, "instance", self.dbobj.name)
        if self.dbobj.service.need_client_list:
            pan_assign(lines, "clients", self.dbobj.client_fqdns)


class PlenaryServiceInstanceClientDefault(SIHelperMixin, Plenary):
    """
    Any client of the service will include this
    template based on service bindings: it will be directly
    included from within the host.tpl. This may
    be overridden within the template library, but this plenary
    should typically be sufficient without override.
    This template defines configuration for clients only, and
    is specific to the instance.
    """

    prefix = "service"

    @classmethod
    def template_name(cls, dbinstance):
        return "%s/%s/%s/client/config" % (cls.prefix, dbinstance.service.name,
                                           dbinstance.name)

    def body(self, lines):
        path = PlenaryServiceInstanceToplevel.template_name(self.dbobj)
        pan_assign(lines, "/system/services/%s" % self.dbobj.service,
                   StructureTemplate(path))

        path = PlenaryServiceClientDefault.template_name(self.dbobj.service)
        pan_include(lines, path)


class PlenaryServiceInstanceServerDefault(SIHelperMixin, Plenary):
    """
    Any server of the servivce will include this
    template based on service bindings: it will be directly
    included from within the host plenary. This may be overridden
    within the template library, but this template should be
    sufficient. The template defines configuration for servers
    only and is specific to the service instance.
    """

    prefix = "service"

    @classmethod
    def template_name(cls, dbinstance):
        return "%s/%s/%s/server/config" % (cls.prefix, dbinstance.service.name,
                                           dbinstance.name)

    def body(self, lines):
        path = PlenaryServiceInstanceServer.template_name(self.dbobj)
        # TODO: we should export the FQDN, IP address, and service address name
        # that provides the service
        # TODO: make it possible to provide multiple instances of the same
        # service
        pan_assign(lines, "/system/provides/%s" % self.dbobj.service,
                   StructureTemplate(path))

        path = PlenaryServiceServerDefault.template_name(self.dbobj.service)
        pan_include(lines, path)
