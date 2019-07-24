#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2017,2019  Contributor
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
"""Contains the logic for `aq del host`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.logger import CLIENT_INFO
from aquilon.notify.index import trigger_notifications
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import hostname_to_host, remove_host
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.change_management import ChangeManagement
from aquilon.aqdb.model import Machine

import aquilon.aqdb.model.hostlifecycle


class CommandDelHost(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["hostname"]
    _default_allowed_status = (
        aquilon.aqdb.model.hostlifecycle.Blind.__mapper_args__[
            'polymorphic_identity'],
        aquilon.aqdb.model.hostlifecycle.Build.__mapper_args__[
            'polymorphic_identity'],
        aquilon.aqdb.model.hostlifecycle.Decommissioned.__mapper_args__[
            'polymorphic_identity'],
        aquilon.aqdb.model.hostlifecycle.Failed.__mapper_args__[
            'polymorphic_identity'],
        aquilon.aqdb.model.hostlifecycle.Install.__mapper_args__[
            'polymorphic_identity']
    )

    def _get_allowed_status(self, archetype, logger):
        section = 'archetype_{}'.format(archetype.name)
        option = 'del_host_buildstatus_allow_only'
        if self.config.has_section(section) and self.config.has_option(
                section, option):
            value = self.config.get(section, option)
            permitted = {s.strip() for s in value.split(',') if s}
            all_buildstatus = set(aquilon.aqdb.model.hostlifecycle
                                  .HostLifecycle.__mapper__.polymorphic_map)
            if not permitted.issubset(all_buildstatus):
                unknown = ', '.join(permitted.difference(all_buildstatus))
                logger.warning(
                    'Invalid buildstatus detected in configuration option '
                    '{option} in section {section}: {unknown}.'.format(
                        option=option, section=section, unknown=unknown))
                permitted.intersection_update(all_buildstatus)
        else:
            permitted = set(self._default_allowed_status)
        return permitted

    def _validate_buildstatus(self, dbhost, logger):
        permitted = self._get_allowed_status(dbhost.archetype, logger)
        msg = ''
        if not permitted:
            msg = ('Current configuration for hosts that belong to archetype '
                   '"{}" does not specify any state in which they could be '
                   'deleted.'.format(dbhost.archetype.name))
            logger.warning(msg)
        if dbhost.status.name not in permitted:
            reason = msg or (
                'In case of archetype "{archetype}", only hosts with the '
                'following status can be deleted: {allowed_status}.'
                .format(archetype=dbhost.archetype.name,
                        allowed_status=', '.join(sorted(permitted))))
            raise ArgumentError(
                'This host status "{host_status}" combined with its archetype '
                'configuration prevents it from being deleted.  {reason}'
                .format(host_status=dbhost.status.name,
                        reason=reason))

    def render(self, session, logger, plenaries, hostname, user,
               justification, reason, exporter, **arguments):
        # Check dependencies, translate into user-friendly message
        dbhost = hostname_to_host(session, hostname)
        dbmachine = dbhost.hardware_entity
        # Only proceed if the host buildstatus allows deletions.
        self._validate_buildstatus(dbhost, logger)

        if not isinstance(dbmachine, Machine):
            raise ArgumentError("Command del_host should only be used for machines, "
                                "but {0} is a {1:cl}.".format(hostname, dbmachine))

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
        cm.consider(dbhost)
        cm.validate()

        if dbhost.virtual_machines:
            machines = ", ".join(sorted(m.label for m in
                                        dbhost.virtual_machines))
            raise ArgumentError("{0} still has virtual machines: {1!s}."
                                .format(dbhost, machines))

        if dbhost.cluster:
            raise ArgumentError("{0} is still a member of {1:l}, and cannot "
                                "be deleted.  Please remove it from the "
                                "cluster first.".format(dbhost, dbhost.cluster))

        # Any service bindings that we need to clean up afterwards

        oldinfo = None
        if dbhost.archetype.name != 'aurora':
            oldinfo = DSDBRunner.snapshot_hw(dbmachine)

        remove_host(logger, dbmachine, plenaries)

        if dbmachine.vm_container:
            plenaries.add(dbmachine.vm_container)

        # In case of Zebra, the IP may be configured on multiple interfaces
        ip = dbmachine.primary_ip
        for iface in dbmachine.interfaces:
            if exporter:
                for addr in iface.assignments:
                    if addr.label:
                        continue
                    for dnr in addr.dns_records:
                        if dnr.reverse_ptr == dbmachine.primary_name.fqdn:
                            exporter.update(dnr.fqdn)
            if ip in iface.addresses:
                iface.addresses.remove(ip)

        dbdns_rec = dbmachine.primary_name
        dbmachine.primary_name = None
        delete_dns_record(dbdns_rec, exporter=exporter)
        session.flush()

        with plenaries.transaction():
            if oldinfo:
                dsdb_runner = DSDBRunner(logger=logger)
                dsdb_runner.update_host(dbmachine, oldinfo)
                dsdb_runner.commit_or_rollback("Could not remove host %s from "
                                               "DSDB" % hostname)
            else:
                logger.client_info("WARNING: removing host %s from AQDB and "
                                   "*not* changing DSDB." % hostname)

        trigger_notifications(self.config, logger, CLIENT_INFO)

        return
