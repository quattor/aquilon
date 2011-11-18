# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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


import re

from aquilon.exceptions_ import AuthorizationException
from aquilon.config import Config

host_re = re.compile(r'^host/(.+)@([^@]+)$')

class AuthorizationBroker(object):
    """Handles any behind the scenes work in figuring out entitlements."""

    # Borg
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state
        self.config = Config()

    def raise_auth_error(self, principal, action, resource):
        auth_msg = self.config.get("broker", "authorization_error")
        raise AuthorizationException("Unauthorized access attempt by %s to %s "
                                     "on %s.  %s" %
                                     (principal, action, resource, auth_msg))

    # FIXME: Hard coded check for now.
    def check(self, principal, dbuser, action, resource):
        if action.startswith('show') or action.startswith('search') \
           or action.startswith('cat') or action == 'status' \
           or action == 'dump_dns':
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
                      'add_grn', 'del_grn', 'update_grn',
                      'rollback']:
            if dbuser.role.name not in ['engineering', 'aqd_admin']:
                raise AuthorizationException(
                    "Must have the engineering or aqd_admin role to %s." %
                    action)
        if action in ['permission']:
            if dbuser.role.name not in ['aqd_admin', 'gatekeeper']:
                raise AuthorizationException(
                    "Must have the gatekeeper or aqd_admin role to %s." %
                    action)
        if action in ['flush']:
            if dbuser.role.name not in ['aqd_admin']:
                raise AuthorizationException(
                    "Must have the aqd_admin role to %s." % action)
        if dbuser.role.name == 'winops':
            if action not in ['add_host', 'add_windows_host', 'make_cluster',
                              'reconfigure']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'winops_server':
            if action not in ['add_windows_host', 'del_windows_host',
                              'add_alias', 'del_alias',
                              'make_cluster', 'reconfigure']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'resource_pool':
            if action not in ['add_address', 'del_address']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'hpevelo':
            if action not in ['reconfigure', 'pxeswitch',
                              'add_disk', 'del_disk', 'del_disk_disk']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'location_admin':
            if action not in ['add_location', 'del_location',
                              'add_building', 'del_building',
                              'add_city', 'del_city']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'telco_operations':
            if action not in ['add_rack', 'add_switch', 'add_tor_switch',
                              'update_rack', 'update_switch',
                              'del_rack', 'del_switch', 'del_tor_switch',
                              'update_router']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'maintech':
            if action not in ['pxeswitch', 'pxeswitch_list',
                              'compile', 'compile_hostname', 'change_status',
                              'update_interface_hostname',
                              'update_interface_machine']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'unixops_l2':
            if action not in ['add_host', 'add_windows_host',
                              'compile', 'compile_hostname',
                              'reconfigure', 'change_status',
                              'reconfigure_list', 'reconfigure_hostlist',
                              'pxeswitch', 'pxeswitch_list',
                              'add_interface_chassis',
                              'add_interface_hostname',
                              'add_interface_machine',
                              'add_reboot_intervention',
                              'add_reboot_schedule',
                              'del_reboot_intervention',
                              'del_reboot_schedule',
                              'update_interface_hostname',
                              'update_interface_machine',
                              'add_machine',
                              'update_machine', 'update_machine_hostname',
                              'add_esx_cluster', 'update_esx_cluster',
                              'bind_esx_cluster_hostname',
                              'rebind_esx_cluster_hostname',
                              'cluster', 'change_status_cluster',
                              'add_manager', 'add_dynamic_range', 'add_disk',
                              'add_auxiliary',
                              'add_service_instance',
                              'update_service_instance',
                              'add_nas_disk_share',
                              'poll_switch', 'poll_tor_switch_tor_switch',
                              'poll_switch_switch', 'poll_tor_switch',
                              'make', 'make_cluster']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'alias_manager':
            if action not in ['add_alias', 'del_alias', 'update_alias']:
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

    def check_network_environment(self, dbuser, dbnet_env):
        """More hacky authorization code.

        This bit is a helper for restricting people from touching networks
        that are maintained in other systems.  That restriction can be
        overridden for a configured list of roles (like aqd_admin) for
        emergencies.

        Something saner should be done here when we have better entitlements.

        """
        if not dbnet_env.is_default:
            # rely on standard authorization for all other environments
            return
        default = self.config.get("site", "default_network_environment")
        conf_value = self.config.get("site", "change_default_netenv_roles")
        allowed_roles = conf_value.strip().split()
        if dbuser.role.name not in allowed_roles:
            raise AuthorizationException("Only users with %s can modify "
                                         "networks in the %s network "
                                         "environment." %
                                         (allowed_roles, default))
        return
