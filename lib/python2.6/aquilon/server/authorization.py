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
"""Authorization stub for simple authorization checks."""


from twisted.python import log

from aquilon.exceptions_ import AuthorizationException
from aquilon.config import Config
from aquilon.server.dbwrappers.user_principal import host_re


class AuthorizationBroker(object):
    """Handles any behind the scenes work in figuring out entitlements."""

    # Borg
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state
        self.config = Config()

    def raise_auth_error(self, principal, action, resource):
        auth_group = self.config.get("broker", "authorization_mailgroup")
        raise AuthorizationException("Unauthorized access attempt by %s to %s "
                                     "on %s.  Request permission from '%s'." %
                                     (principal, action, resource, auth_group))

    # FIXME: Hard coded check for now.
    def check(self, principal, dbuser, action, resource):
        if action.startswith('show') or action.startswith('search') \
           or action.startswith('cat') or action == 'status':
            return True
        if dbuser is None:
            raise AuthorizationException(
                    "Unauthorized anonymous access attempt to %s on %s" %
                    (action, resource))
        # Special-casing the aquilon hosts... this is a special user
        # that provides a bucket for all host-generated activity.
        if self._check_aquilonhost(principal, dbuser, action, resource):
            return True
        if dbuser.role.name == 'nobody':
            self.raise_auth_error(principal, action, resource)
        # Right now, anybody in a group can do anything they want, except...
        if action in ['add_archetype', 'update_archetype', 'del_archetype',
                      'add_vendor', 'del_vendor',
                      'add_os', 'del_os',
                      'add_model', 'update_model', 'del_model',
                      'add_organization', 'del_organization',
                      'rollback']:
            if dbuser.role.name not in ['engineering', 'aqd_admin']:
                raise AuthorizationException(
                    "Must have the engineering or aqd_admin role to %s." %
                    action)
        if action in ['permission', 'flush', 'add_network', 'del_network']:
            if dbuser.role.name not in ['aqd_admin']:
                raise AuthorizationException(
                    "Must have the aqd_admin role to %s." % action)
        if dbuser.role.name == 'winops':
            if action not in ['add_host', 'add_windows_host', 'make_cluster',
                              'reconfigure']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'location_admin':
            if action not in ['add_location', 'del_location',
                              'add_building', 'del_building',
                              'add_city', 'del_city']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'maintech':
            if action not in ['pxeswitch', 'pxeswitch_list',
                              'compile', 'compile_hostname', 'change_status',
                              'update_interface_hostname',
                              'update_interface_machine']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'unixops_l2':
            if action not in ['add_host',
                              'compile', 'compile_hostname',
                              'reconfigure', 'change_status',
                              'reconfigure_list', 'reconfigure_hostlist',
                              'pxeswitch', 'pxeswitch_list',
                              'add_interface_chassis',
                              'add_interface_hostname',
                              'add_interface_machine',
                              'update_interface_hostname',
                              'update_interface_machine',
                              'add_machine',
                              'update_machine', 'update_machine_hostname',
                              'add_esx_cluster', 'update_esx_cluster',
                              'bind_esx_cluster_hostname',
                              'rebind_esx_cluster_hostname',
                              'cluster',
                              'add_manager', 'add_dynamic_range', 'add_disk',
                              'add_auxiliary',
                              'make', 'make_cluster']:
                self.raise_auth_error(principal, action, resource)
        return True

    def _check_aquilonhost(self, principal, dbuser, action, resource):
        """ Return true if the incoming user is an aquilon host and this is
            one of the few things that a host is allowed to change on its
            own."""
        if dbuser.name != 'aquilonhost':
            return False
        m = host_re.match(principal)
        if not m:
            return False
        if resource.startswith("/host/%s/" % m.group(1)):
            return True
        return False
