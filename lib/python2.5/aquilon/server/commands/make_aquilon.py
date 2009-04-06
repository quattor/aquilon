# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq make aquilon`."""


from os import path as os_path, environ as os_environ
from socket import gethostbyname

from aquilon.exceptions_ import (ProcessException, DetailedProcessException,
                                 ArgumentError, NameServiceError, AquilonError)
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.cfg_path import get_cfg_path
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.dbwrappers.status import get_status
from aquilon.aqdb.sy.build_item import BuildItem
from aquilon.server.templates.domain import TemplateDomain
from aquilon.server.templates.base import compileLock, compileRelease
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.services import Chooser

class CommandMakeAquilon(BrokerCommand):

    required_parameters = ["hostname", "os"]

    def render(self, session, hostname, os, personality, buildstatus,
               debug, user, **arguments):
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

        # We grab a template compile lock over this whole operation,
        # which means that we will wait until any outstanding compiles
        # have completed before we start modifying files within template
        # domains.
        old_content = None
        chooser = None
        try:
            compileLock()
            plenary_host = PlenaryHost(dbhost)

            try:
                old_content = plenary_host.read()
            except IOError, e:
                # Sigh, it's an IOError if the file doesn't exist.
                old_content = None

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
                session.add(dbos_bi)

            if personality:
                # Yes, the current archetype is assumed from the old
                # personality...
                dbpersonality = get_personality(session, dbhost.archetype.name,
                                                personality)
                dbhost.personality = dbpersonality

            if buildstatus:
                dbstatus = get_status(session, buildstatus)
                dbhost.status = dbstatus
                session.add(dbhost)

            session.flush()
            #session.refresh(dbhost)

            if arguments.get("keepbindings", None):
                chooser = Chooser(dbhost, required_only=False, debug=debug)
            else:
                chooser = Chooser(dbhost, required_only=True, debug=debug)
            chooser.set_required()
            chooser.flush_changes()
            chooser.write_plenary_templates(locked=True)

            plenary_host = PlenaryHost(dbhost)
            plenary_host.write(locked=True)

            td = TemplateDomain(dbhost.domain)
            out = td.compile(session, only=dbhost, locked=True)

        except:
            # If this was a change, then we need to revert the plenary,
            # to avoid this domain being un-compilable in the future.
            # If this was a new file, we can just remove the plenary.
            if (old_content is None):
                plenary_host.remove(locked=True)
            else:
                # this method corrupts the mtime, which will cause this
                # host to be compiled next time from a normal "make".
                plenary_host.write(locked=True, content=old_content)

            # Black magic... need to find out if sqlalchemy objects
            # will re-vivify after a rollback based on id.
            if chooser:
                session.rollback()
                chooser.write_plenary_templates(locked=True)

            # Okay, cleaned up templates, make sure the caller knows
            # we've aborted so that DB can be appropriately rollback'd.

            # Error will not include any debug output...
            raise

        finally:
            compileRelease()

        # This command does not use a formatter.  Maybe it should.
        if chooser and chooser.debug_info:
            return str("\n".join(chooser.debug_info + [out]))
        return str(out)


