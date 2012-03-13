# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
from aquilon.worker.templates.panutils import pan, StructureTemplate
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
    def __init__(self, dbservice, logger=LOGGER):
        Plenary.__init__(self, dbservice, logger=logger)
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
    def __init__(self, dbservice, logger=LOGGER):
        Plenary.__init__(self, dbservice, logger=logger)
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
    def __init__(self, dbservice, logger=LOGGER):
        Plenary.__init__(self, dbservice, logger=logger)
        self.name = dbservice.name
        self.plenary_core = "service/%(name)s/server" % self.__dict__
        self.plenary_template = "%(plenary_core)s/config" % self.__dict__
        self.template_type = ''
        self.dir = self.config.get("broker", "plenarydir")


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
        if dbinstance.service.name == 'nas_disk_share':
            self.plenaries.append(PlenaryInstanceNasDiskShare(dbinstance,
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
    def __init__(self, dbinstance, logger=LOGGER):
        Plenary.__init__(self, dbinstance, logger=logger)
        self.service = dbinstance.service.name
        self.name = dbinstance.name
        self.plenary_core = "servicedata/%(service)s/%(name)s" % self.__dict__
        self.plenary_template = self.plenary_core + "/config"
        self.template_type = 'structure'
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        lines.append("include { 'servicedata/%(service)s/config' };" % self.__dict__)
        lines.append("")
        lines.append('"instance" = %s;' % pan(self.name))
        lines.append('"servers" = %s;' % pan(self.dbobj.server_fqdns))
        if self.service == 'dns':
            lines.append('"server_ips" = %s;' % pan(self.dbobj.server_ips))


class PlenaryServiceInstanceServer(Plenary):
    """
    This structure template provides information for the template
    specific to the service instance and for use by the server.
    This data is separated away from the PlenaryServiceInstanceServerDefault
    to allow that template to be overridden in the template library
    while still having access to the generated data here (the list
    of clients and the instance name)
    """
    def __init__(self, dbinstance, logger=LOGGER):
        Plenary.__init__(self, dbinstance, logger=logger)
        self.service = dbinstance.service.name
        self.name = dbinstance.name
        self.plenary_core = "servicedata/%(service)s/%(name)s" % self.__dict__
        self.plenary_template = self.plenary_core + "/srvconfig"
        self.template_type = 'structure'
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        lines.append('"instance" = %s;' % pan(self.name))
        lines.append('"clients" = %s;' % pan(self.dbobj.client_fqdns))


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
    def __init__(self, dbinstance, logger=LOGGER):
        Plenary.__init__(self, dbinstance, logger=logger)
        self.service = dbinstance.service.name
        self.name = dbinstance.name
        self.plenary_core = "service/%(service)s/%(name)s/client" % self.__dict__
        self.plenary_template = self.plenary_core + "/config"
        self.template_type = ''
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        lines.append('"/system/services/%s" = %s;' %
                     (self.service, pan(StructureTemplate('servicedata/%s/%s/config' %
                                                          (self.service,
                                                           self.name)))))
        lines.append("include { 'service/%s/client/config' };" % self.service)


class PlenaryServiceInstanceServerDefault(Plenary):
    """
    Any server of the servivce will include this
    template based on service bindings: it will be directly
    included from within the host.tpl. This may be overridden
    within the template library, but this template should be
    sufficient. The template defines configuration for servers
    only and is specific to the service instance.
    """
    def __init__(self, dbinstance, logger=LOGGER):
        Plenary.__init__(self, dbinstance, logger=logger)
        self.service = dbinstance.service.name
        self.name = dbinstance.name
        self.plenary_core = "service/%(service)s/%(name)s/server" % self.__dict__
        self.plenary_template = self.plenary_core + "/config"
        self.template_type = ''
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        lines.append('"/system/provides/%s" = %s;' %
                     (self.service, pan(StructureTemplate('servicedata/%s/%s/srvconfig' %
                                                          (self.service,
                                                           self.name)))))
        lines.append("include { 'service/%s/server/config' };" % self.service)


class PlenaryInstanceNasDiskShare(Plenary):
    """
    A service instance of the nas_disk_share type wants to have a
    struct template that can be imported into the disk definition to get
    sufficient information to be able to know whence to mount the disk.
    This class needs to be in sync with the consumer PlenaryMachine
    """
    def __init__(self, dbinstance, logger=LOGGER):
        Plenary.__init__(self, dbinstance, logger=logger)
        self.service = dbinstance.service.name
        self.name = dbinstance.name
        self.plenary_core = "service/%(service)s/%(name)s/client" % self.__dict__
        self.plenary_template = self.plenary_core + "/nasinfo"
        self.template_type = 'structure'
        self.dir = self.config.get("broker", "plenarydir")
        self.server = ""
        self.mount = ""

    def body(self, lines):
        """
        dynamically produce content of template, based on external lookup.
        If the external lookup fails, this can raise a NotFoundException,
        a ProcessException or an IOError
        """
        self.lookup()
        if self.server == "":
            # TODO: We should really invoke a realtime-check by running
            # the command defined in the broker config. The output
            # of "nasti show share --csv" is in CSV format (why it
            # doesn't provide the same format as the dumpfile is
            # beyond me). We need a CSV parser...
            raise NotFoundException("Share %s cannot be found in NAS maps." %
                                    self.name)
        lines.append('"sharename" = %s;' % pan(self.name))
        lines.append('"server" = %s;' % pan(self.server))
        lines.append('"mountpoint" = %s;' % pan(self.mount))

    def lookup(self):
        with open(self.config.get("broker", "sharedata")) as sharedata:
            find_storage_data(sharedata, lambda inf: self.check_nas_line(inf))

    def check_nas_line(self, inf):
        """
        Search for the pshare info that refers to this plenary
        """
        # silently discard lines that don't have all of our reqd info.
        for k in ["objtype", "pshare", "server", "dg"]:
            if k not in inf:
                return False

        if inf["objtype"] == "pshare" and inf["pshare"] == self.name:
            self.server = inf["server"]
            self.mount = "/vol/%(dg)s/%(pshare)s" % (inf)
            return True
        else:
            return False


# This should come from some external API...?
def find_storage_data(datafile, fn):
    """
    Scan a storeng-style data file, checking each line as we go

    Storeng-style data files are blocks of data. Each block starts
    with a comment describing the fields for all subsequent lines. A
    block can start at any time. Fields are separated by '|'.
    This function will invoke the function after parsing every data
    line. The function will be called with a dict of the fields. If the
    function returns True, then we stop scanning the file, else we continue
    on until there is nothing left to parse.
    """
    for line in datafile:
        line = line.rstrip()
        if line[0] == '#':
            # A header line
            hdr = line[1:].split('|')
        else:
            fields = line.split('|')
            if len(fields) == len(hdr):  # silently ignore invalid lines
                info = dict()
                for i in range(0, len(hdr)):
                    info[hdr[i]] = fields[i]
                if (fn(info)):
                    break
