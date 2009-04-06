# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains a wrapper for `aq reconfigure`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.make_aquilon import CommandMakeAquilon
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.dbwrappers.status import get_status
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.aqdb.sy.build_item import BuildItem
from aquilon.exceptions_ import ArgumentError


class CommandReconfigure(CommandMakeAquilon):
    """The make aquilon command already contains the logic required."""

    required_parameters = ["hostname"]

    def render(self, session, hostname, os, personality, buildstatus,
               **arguments):
        """There is some duplication here with make_aquilon.

        It seemed to be the cleanest way to allow non-aquilon hosts
        to use reconfigure for buildstatus and personality.

        """
        dbhost = hostname_to_host(session, hostname)

        if dbhost.archetype.name == 'aquilon':
            # For aquilon hosts, check if make_aquilon has run.  (This
            # is a lame check - should really check to see if OS is set.)
            # If the error is not raised, we fall through to the end
            # of the method where MakeAquilon is called.
            builditem = session.query(BuildItem).filter_by(host=dbhost).first()
            if not builditem:
                raise ArgumentError("host %s has not been built. "
                                    "Run 'make_aquilon' first." % hostname)
        # The rest of these conditionals currently apply to all
        # non-aquilon hosts.
        elif os:
            raise ArgumentError("Can only set os for "
                                "hosts with archetype aquilon.")
        elif buildstatus or personality:
            if buildstatus:
                dbstatus = get_status(session, buildstatus)
                dbhost.status = dbstatus
            if personality:
                dbpersonality = get_personality(session, dbhost.archetype.name,
                                                personality)
                dbhost.personality = dbpersonality
            session.add(dbhost)
            return
        else:
            raise ArgumentError("Nothing to do.")

        return CommandMakeAquilon.render(self, session=session,
                                         hostname=hostname, os=os,
                                         personality=personality,
                                         buildstatus=buildstatus, **arguments)


