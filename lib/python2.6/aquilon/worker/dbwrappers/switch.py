# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2012  Contributor
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
""" Helper functions for managing switches """


from random import choice

from aquilon.exceptions_ import InternalError
from aquilon.aqdb.model import Service, ServiceInstance


def determine_helper_hostname(session, logger, config, dbswitch):
    """Try to figure out a useful helper from the mappings.
    """
    helper_name = config.get("broker", "poll_helper_service")
    if not helper_name:  # pragma: no cover
        return
    helper_service = Service.get_unique(session, helper_name,
                                        compel=InternalError)
    mapped_instances = ServiceInstance.get_mapped_instance_cache(
        dbpersonality=None, dblocation=dbswitch.location,
        dbservices=[helper_service])
    for dbsi in mapped_instances.get(helper_service, []):
        if dbsi.server_hosts:
            # Poor man's load balancing...
            jump = choice(dbsi.server_hosts).fqdn
            logger.client_info("Using jump host {0} from {1:l} to run CheckNet "
                               "for {2:l}.".format(jump, dbsi, dbswitch))
            return jump

    logger.client_info("No jump host for %s, calling CheckNet from %s." %
                       (dbswitch, config.get("broker", "hostname")))
    return None


def determine_helper_args(config):
    ssh_command = config.get("broker", "poll_ssh").strip()
    if not ssh_command:  # pragma: no cover
        return []
    ssh_args = [ssh_command]
    ssh_options = config.get("broker", "poll_ssh_options")
    ssh_args.extend(ssh_options.strip().split())
    return ssh_args
