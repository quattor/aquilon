#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show personality --name`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.commands.show_location_type import CommandShowLocationType
from aquilon.aqdb.cfg.cfg_path import CfgPath

class CommandShowPersonality(BrokerCommand):

    required_parameters = []

    @add_transaction
    @az_check
    @format_results
    def render(self, session, name, **arguments):
        # This is a bit ick for now, since personalities don't have their
        # own table, instead they're just entries in the cfgpath. Ideally,
        # we'd be looking in the Personality table and one of the attributes
        # there would be the cfgpath.
        try:
            all = session.query(CfgPath).filter_by(relative_path=name).join('tld').filter_by(type="personality").one()
        except InvalidRequestError, e:
            raise NotFoundException("Personality '%s' not found: %s" % (name, e))
            
        return all


#if __name__=='__main__':
