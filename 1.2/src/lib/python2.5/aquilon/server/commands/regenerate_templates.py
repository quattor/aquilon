#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq regenerate_templates`."""


from aquilon.exceptions_ import UnimplementedError, PartialError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.aqdb.hardware import Machine
from aquilon.server.templates import PlenaryMachineInfo


class CommandRegenerateTemplates(BrokerCommand):

    required_parameters = ["all"]

    @add_transaction
    @az_check
    def render(self, session, all, user, **arguments):
        if not all:
            raise UnimplementedError("The regenerate templates command has only been implemented for --all")
        plenarydir = self.config.get("broker", "plenarydir")
        servername = self.config.get("broker", "servername")
        hostsdir = self.config.get("broker", "hostsdir")
        success = []
        failed = []
        for dbmachine in session.query(Machine).all():
            try:
                plenary_info = PlenaryMachineInfo(dbmachine)
                plenary_info.write(plenarydir, servername, user)
            except Exception, e:
                failed.append("Machine %s FAILED: %s" % (dbmachine.name, e))
                if dbmachine.host:
                    failed.append(
                            "Host %s FAILED: Depends on FAILED Machine %s" %
                            (dbmachine.host.fqdn, dbmachine.name))
                continue
            if dbmachine.host:
                try:
                    plenary_info.reconfigure(dbmachine.host, hostsdir,
                            servername, user)
                except Exception, e:
                    failed.append("Host %s FAILED: %s" %
                            (dbmachine.host.fqdn, e))
        if failed:
            raise PartialError(success, failed)
        return


#if __name__=='__main__':
