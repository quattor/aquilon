# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Wrappers to make getting and using hosts simpler."""


from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import Machine


def hostname_to_host(session, hostname):
    dbmachine = Machine.get_unique(session, hostname, compel=True)
    if not dbmachine.host:
        raise NotFoundException("{0} does not have a host "
                                "assigned.".format(dbmachine))
    return dbmachine.host

def get_host_build_item(self, dbhost, dbservice):
    for template in dbhost.templates:
        si = template.service_instance
        if si and si.service == dbservice:
            return template
    return None

def get_host_dependencies(session, dbhost):
    """ returns a list of strings describing how a host is being used.
    If the host has no dependencies, then an empty list is returned
    """
    ret = []
    for sis in dbhost.services_provided:
        ret.append("%s is bound as a server for service %s instance %s" %
                   (sis.host.fqdn, sis.service_instance.service.name,
                    sis.service_instance.name))
    if dbhost.cluster and hasattr(dbhost.cluster, 'vm_to_host_ratio') and \
       dbhost.cluster.host_count * len(dbhost.cluster.machines) > \
       dbhost.cluster.vm_count * (len(dbhost.cluster.hosts) - 1):
           ret.append("Removing vmhost %s from %s cluster %s would exceed "
                      "vm_to_host_ratio %s (%s VMs:%s hosts)" %
                      (dbhost.fqdn, dbhost.cluster.cluster_type,
                       dbhost.cluster.name, dbhost.cluster.vm_to_host_ratio,
                       len(dbhost.cluster.machines),
                       len(dbhost.cluster.hosts) - 1))
    return ret
