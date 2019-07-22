# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2019  Contributor
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
"""Contains the logic for `aq add shared service name`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # noqa
from aquilon.worker.commands.add_resource import CommandAddResource
from aquilon.aqdb.model import (
    AddressAlias,
    BundleResource,
    Fqdn,
    ResourceGroup,
    SharedServiceName,
)


class CommandAddSharedServiceName(CommandAddResource):

    required_parameters = ['fqdn', 'name', 'resourcegroup', 'sa_aliases']
    resource_class = SharedServiceName
    resource_name = 'name'

    def render(self, **kwargs):
        # This command deliberately does not allow the resource holder to
        # be specified as anything other than a resource-group, so fill in
        # the missing ones here.
        for h in ('hostname', 'cluster', 'metacluster', 'personality',
                  'archetype', 'eon_id', 'grn'):
            kwargs[h] = None

        super(CommandAddSharedServiceName, self).render(**kwargs)

    def setup_resource(self, session, logger, dbres, reason,
                       fqdn, sa_aliases, dns_environment, **_):
        # ensure this belongs in a resource-group;  use the fact the
        # holder is already determined
        if (not isinstance(dbres.holder, BundleResource) or
                not isinstance(dbres.holder.resourcegroup, ResourceGroup)):
            raise ArgumentError("{0} must be in a resource-group "
                                "(got {1:c})".format(dbres, dbres.holder))

        # ensure no other shared-service-name resource than ourself is present
        # in the group.
        for res in dbres.holder.resources:
            if isinstance(res, SharedServiceName) and (res != dbres):
                raise ArgumentError("{0} already has a {1:c} resource".
                                    format(dbres.holder.resourcegroup, res))

        dbfqdn = Fqdn.get_or_create(session, dns_environment=dns_environment,
                                    fqdn=fqdn)

        # if sa_aliases is true, ensure the FQDN is unique except for
        # address-aliases; if sa_aliases is false, no DNS records using
        # that (LHS) may exist.
        for dnsrec in dbfqdn.dns_records:
            if not sa_aliases or not isinstance(dnsrec, AddressAlias):
                raise ArgumentError("{0:s} cannot be used as a shared "
                                    "service name FQDN, as {1} already "
                                    "exists".format(fqdn, dnsrec))
        if dbfqdn.shared_service_names:
            raise ArgumentError("{0:s} cannot be used as a shared service "
                                "name FQDN, as {1} already exists"
                                .format(fqdn, dbfqdn.shared_service_names[0]))

        dbres.sa_aliases = sa_aliases
        dbres.fqdn = dbfqdn
