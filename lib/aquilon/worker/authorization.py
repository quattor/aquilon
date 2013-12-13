# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
                      'add_organization', 'del_organization',
                      'add_grn', 'del_grn', 'update_grn',
                      'add_vlan', 'del_vlan',
                      'rollback', 'update_city']:
            if dbuser.role.name not in ['engineering', 'aqd_admin']:
                raise AuthorizationException(
                    "Must have the engineering or aqd_admin role to %s." %
                    action)
        if action in ['add_vendor', 'del_vendor',
                      'add_os', 'update_os', 'del_os',
                      'add_model', 'update_model', 'del_model']:
            if dbuser.role.name not in ['engineering', 'aqd_admin',
                                        'network_engineering']:
                raise AuthorizationException(
                    "Must have the engineering, network_engineering or "
                    "aqd_admin role to %s." % action)
        if action in ['permission']:
            if dbuser.role.name not in ['aqd_admin', 'gatekeeper']:
                raise AuthorizationException(
                    "Must have the gatekeeper or aqd_admin role to %s." %
                    action)
        if action in ['flush', 'refresh_windows_hosts']:
            if dbuser.role.name not in ['aqd_admin']:
                raise AuthorizationException(
                    "Must have the aqd_admin role to %s." % action)
        if dbuser.role.name == 'winops':
            if action not in ['add_host', 'add_windows_host', 'make_cluster',
                              'reconfigure', 'update_machine']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'winops_server':
            # Only need add/update_cluster for hacluster VCenters
            if action not in ['add_windows_host', 'del_windows_host',
                              'add_aurora_host',
                              'add_alias', 'update_alias', 'del_alias',
                              'add_machine', 'add_host',
                              'add_interface_hostname',
                              'add_interface_machine',
                              'add_interface_address',
                              'add_address', 'del_address',
                              'reconfigure',
                              'add_cluster', 'make_cluster', 'update_cluster',
                              'change_status', 'change_status_cluster',
                              'add_service_instance', 'map_service',
                              'bind_server', 'update_machine']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'mssb_unixops':
            if action not in ['add_machine', 'del_machine',
                              'update_machine', 'update_machine_hostname',
                              'add_interface_hostname',
                              'add_interface_machine',
                              'add_interface_address',
                              'add_interface_chassis',
                              'update_interface_hostname',
                              'update_interface_machine',
                              'del_interface', 'del_interface_address',
                              'add_alias', 'update_alias', 'del_alias',
                              'add_address', 'del_address',
                              'add_host', 'del_host',
                              'add_windows_host', 'del_windows_host',
                              'add_manager', 'add_dynamic_range', 'add_disk',
                              'add_auxiliary',
                              'del_manager', 'del_auxiliary',
                              'del_disk', 'del_disk_disk', 'update_disk',
                              'add_filesystem', 'del_filesystem',
                              'add_rack', 'add_rack_room', 'add_chassis',
                              'del_rack', 'del_chassis',
                              'map_grn', 'unmap_grn',
                              'change_status']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'spot_server':
            if action not in ['add_machine', 'del_machine',
                              'add_machine_prefix',
                              'add_interface_hostname',
                              'add_interface_machine',
                              'add_interface_address',
                              'del_interface', 'del_interface_address',
                              'add_address', 'del_address',
                              'add_host', 'del_host',
                              'add_alias', 'del_alias',
                              'make', 'make_cluster',
                              'pxeswitch',
                              'change_status',
                              'add_room', 'add_rack', 'add_rack_room',
                              'add_disk', 'del_disk', 'del_disk_disk',
                              'update_disk']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'resource_pool':
            if action not in ['add_address', 'del_address']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'secadmin':
            if action not in ['permission']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'hpevelo':
            if action not in ['reconfigure', 'pxeswitch', 'change_status',
                              'add_disk', 'del_disk', 'del_disk_disk',
                              'update_disk']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'location_admin':
            if action not in ['add_building', 'del_building',
                              'add_city', 'del_city']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'telco_operations':
            if action not in ['add_rack', 'add_switch',
                              'update_rack', 'update_switch',
                              'del_rack', 'del_switch',
                              'add_interface_switch', 'del_interface_switch',
                              'update_interface_switch',
                              'add_interface_address_switch',
                              'del_interface_address_switch',
                              'add_alias', 'del_alias',
                              'refresh_network',
                              'update_router']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'network_engineering':
            if action not in ['add_vendor', 'del_vendor',
                              'add_os', 'update_os', 'del_os',
                              'add_model', 'update_model', 'del_model',
                              'add_rack', 'add_switch',
                              'update_rack', 'update_switch',
                              'del_rack', 'del_switch',
                              'add_interface_switch', 'del_interface_switch',
                              'update_interface_switch',
                              'add_interface_address_switch',
                              'del_interface_address_switch',
                              'add_alias', 'del_alias',
                              'refresh_network',
                              'update_router']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'edc':
            if action not in ['add_rack', 'add_machine', 'add_host',
                              'add_interface_machine',
                              'add_interface_hostname',
                              'add_interface_address',
                              'add_alias', 'add_manager',
                              'add_service_address',
                              'del_service_address',
                              'update_rack', 'update_machine', 'update_alias',
                              'update_interface_hostname',
                              'update_interface_machine',
                              'del_rack', 'del_machine', 'del_host',
                              'del_interface', 'del_interface_address',
                              'del_alias', 'del_manager']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'maintech':
            if action not in ['pxeswitch', 'pxeswitch_list',
                              'compile', 'compile_hostname', 'change_status',
                              'update_interface_hostname',
                              'update_interface_machine']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'template_admin':
            if action not in ['add_sandbox', 'del_sandbox',
                              'manage', 'publish', 'reconfigure']:
                self.raise_auth_error(principal, action, resource)

        if dbuser.role.name == 'laf':
            if action not in ['reconfigure',
                              'add_reboot_intervention',
                              'compile_hostname', 'compile_personality',
                              'add_reboot_schedule',
                              'del_reboot_intervention',
                              'del_reboot_schedule',
                              'map_grn', 'unmap_grn',
                              'unmap_grn_clearall',
                              'add_hostlink', 'del_hostlink',
                              'add_personality', 'update_personality',
                              'del_personality',
                              'add_parameter', 'update_parameter',
                              'del_parameter',
                              'bind_feature', 'unbind_feature',
                              'map_service',
                              'add_alias', 'del_alias', 'update_alias']:
                self.raise_auth_error(principal, action, resource)

        if dbuser.role.name == 'itsec':
            if action not in ['pxeswitch', 'pxeswitch_list',
                              'compile', 'compile_hostname',
                              'change_status', 'make',
                              'reconfigure',
                              'reconfigure_list',
                              'reconfigure_hostlist',
                              'add_interface_machine',
                              'add_interface_hostname',
                              'add_interface_address',
                              'update_interface_hostname',
                              'update_interface_machine',
                              'del_interface', 'del_interface_address',
                              'add_disk', 'del_disk', 'del_disk_disk',
                              'update_disk',
                              'add_machine', 'del_machine',
                              'update_machine', 'update_machine_hostname',
                              'add_host', 'del_host',
                              'add_alias', 'add_manager',
                              'del_alias', 'del_manager']:
                self.raise_auth_error(principal, action, resource)

        if dbuser.role.name == 'unixops_l2':
            if action not in ['add_host', 'add_windows_host',
                              'del_host', 'del_windows_host',
                              'compile', 'compile_hostname',
                              'compile_cluster', 'compile_personality',
                              'reconfigure', 'change_status',
                              'reconfigure_list', 'reconfigure_hostlist',
                              'pxeswitch', 'pxeswitch_list',
                              'add_interface_chassis',
                              'add_interface_hostname',
                              'add_interface_machine',
                              'add_interface_address',
                              'del_interface',
                              'del_interface_address',
                              'add_reboot_intervention',
                              'add_reboot_schedule',
                              'del_reboot_intervention',
                              'del_reboot_schedule',
                              'update_interface_hostname',
                              'update_interface_machine',
                              'add_machine',
                              'del_machine',
                              'update_machine', 'update_machine_hostname',
                              'add_cluster', 'update_cluster',
                              'del_cluster',
                              'add_esx_cluster', 'update_esx_cluster',
                              'del_esx_cluster',
                              'bind_esx_cluster_hostname',
                              'rebind_esx_cluster_hostname',
                              'cluster', 'uncluster', 'change_status_cluster',
                              'add_manager', 'add_dynamic_range', 'add_disk',
                              'add_auxiliary',
                              'del_manager', 'del_auxiliary',
                              'del_disk', 'del_disk_disk', 'update_disk',
                              'add_service_instance',
                              'update_service_instance',
                              'del_service_instance',
                              'add_alias', 'del_alias',
                              'update_alias',
                              'add_filesystem',
                              'del_filesystem',
                              'poll_switch', 'poll_switch_switch',
                              'add_rack', 'add_rack_room', 'add_chassis',
                              'del_rack', 'del_chassis',
                              'add_bunker', 'del_bunker',
                              'add_address', 'del_address',
                              'add_personality', 'update_personality',
                              'del_personality',
                              'add_parameter', 'update_parameter',
                              'del_parameter', 'add_required_service',
                              'add_required_service_personality',
                              'bind_feature', 'unbind_feature',
                              'validate_parameter',
                              'add_hostlink', 'del_hostlink',
                              'add_static_route',
                              'del_static_route',
                              'manage_hostname', 'manage_list',
                              'manage_cluster',
                              'map_grn', 'unmap_grn',
                              'make', 'make_cluster']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'alias_manager':
            if action not in ['add_alias', 'del_alias', 'update_alias']:
                self.raise_auth_error(principal, action, resource)
        if dbuser.role.name == 'webops':
            if action not in ['add_address', 'del_address',
                              'update_address',
                              'add_alias', 'del_alias', 'update_alias']:
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
