# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq make aquilon`."""


from os import path as os_path, environ as os_environ
from tempfile import mkdtemp
from socket import gethostbyname

from aquilon.exceptions_ import (ProcessException, DetailedProcessException,
                                 ArgumentError, NameServiceError)
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.cfg_path import get_cfg_path
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.dbwrappers.service_instance import choose_service_instance
from aquilon.server.dbwrappers.status import get_status
from aquilon.aqdb.cfg.cfg_path import CfgPath
from aquilon.aqdb.cfg.tld import Tld
from aquilon.aqdb.sy.build_item import BuildItem
from aquilon.server.templates.domain import TemplateDomain


class CommandMakeAquilon(BrokerCommand):

    required_parameters = ["hostname", "os", "personality"]

    @add_transaction
    @az_check
    def render(self, session, hostname, os, personality, buildstatus,
               user, **arguments):
        dbhost = hostname_to_host(session, hostname)

        # Right now configuration won't work if the host doesn't resolve.  If/when aii is fixed, this should
        # be change to a warning.  The check should only be made in prod though (which also means there's no unittest)
        if self.config.get("broker", "environment") == "prod":
            try:
                gethostbyname(dbhost.fqdn)
            except Exception, e:
                raise NameServiceError("Could not (yet) resolve the name for %s externally, so a build would fail.  Please try again later.  Exact error: %s" %
                        (dbhost.fqdn, e))

        # This could be smarter... maybe go ahead and allow conversion to
        # the aquilon archetype if everything below succeeds.  For now,
        # keeping it simple.
        if dbhost.archetype.name != 'aquilon':
            raise ArgumentError("Host %s has archetype %s, needs to be aquilon for command to succeed." %
                    (hostname, dbhost.archetype.name))

        # Currently, for the Host to be created it *must* be associated with
        # a Machine already.  If that ever changes, need to check here and
        # bail if dbhost.machine does not exist.

        # Need to get all the BuildItem objects for this host.
        # They should include:
        # - exactly one OS
        # - exactly one personality
        # And may include:
        # - many services
        # - many features?

        if os:
            dbos = get_cfg_path(session, "os", os)
            dbos_bi = session.query(BuildItem).filter_by(host=dbhost).join(
                'cfg_path').filter_by(tld=dbos.tld).first()
            if dbos_bi:
                dbos_bi.cfg_path = dbos
            else:
                # FIXME: This could fail if there is already an item at 0
                dbos_bi = BuildItem(host=dbhost, cfg_path=dbos, position=0)
            session.save_or_update(dbos_bi)

        if personality:
            dbpersonality = get_cfg_path(session, "personality", personality)
            dbpersonality_bi = session.query(BuildItem).filter_by(host=dbhost).join(
                'cfg_path').filter_by(tld=dbpersonality.tld).first()
            if dbpersonality_bi:
                dbpersonality_bi.cfg_path = dbpersonality
            else:
                # FIXME: This could fail if there is already an item at 1
                dbpersonality_bi = BuildItem(host=dbhost,
                        cfg_path=dbpersonality, position=1)
            session.save_or_update(dbpersonality_bi)

        if buildstatus:
            dbstatus = get_status(session, buildstatus)
            dbhost.status = dbstatus
            session.update(dbhost)

        session.flush()
        session.refresh(dbhost)
        dbservice_tld = session.query(Tld).filter_by(type='service').one()
        for item in dbhost.archetype.service_list:
            dbservice_bi = session.query(BuildItem).filter_by(
                    host=dbhost).join('cfg_path').filter_by(
                    tld=dbservice_tld).filter(CfgPath.relative_path.like(
                    item.service.name + '/%')).first()
            if dbservice_bi:
                continue
            dbinstance = choose_service_instance(session, dbhost, item.service)
            dbservice_bi = BuildItem(host=dbhost, cfg_path=dbinstance.cfg_path,
                    position=3)
            dbhost.templates.append(dbservice_bi)
            dbhost.templates._reorder()
            session.save(dbservice_bi)

        session.flush()
        session.refresh(dbhost)
        session.refresh(dbhost.machine)

        td = TemplateDomain()
        return td.compile(session, dbhost.domain, user, only=dbhost)


