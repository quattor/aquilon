# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show personality`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.show_location_type import CommandShowLocationType
from aquilon.aqdb.cfg.cfg_path import CfgPath


class CommandShowPersonality(BrokerCommand):

    required_parameters = []

    def render(self, session, **arguments):
        # This is a bit ick for now, since personalities don't have their
        # own table, instead they're just entries in the cfgpath. Ideally,
        # we'd be looking in the Personality table and one of the attributes
        # there would be the cfgpath.
        all = session.query(CfgPath).join('tld').filter_by(type="personality").all()
        return all


