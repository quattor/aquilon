#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del personality`."""


import os

from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.exceptions_ import ArgumentError
from aquilon.server.commands.del_location import CommandDelLocation
from aquilon.aqdb.cfg.cfg_path import CfgPath
from aquilon.aqdb.sy.build_item import BuildItem
from aquilon.aqdb.cfg.tld import Tld
from aquilon.server.templates.personality import PlenaryPersonality


class CommandDelPersonality(BrokerCommand):

    required_parameters = ["name", "archetype"]

    @add_transaction
    @az_check
    def render(self, session, name, archetype, **arguments):
        dbtld = session.query(Tld).filter_by(type="personality").first()

        existing = session.query(CfgPath).filter_by(relative_path=name, tld=dbtld).all()
        if (len(existing) == 0):
            raise ArgumentError("personality '%s' is unknown"%name)
        
        # Check dependencies.
        dbbuilds = session.query(BuildItem).filter_by(cfg_path=existing[0]).all()
        if (len(dbbuilds) > 0):
            raise ArgumentError("personality '%s' is in use and cannot be deleted"%name)

        # All clear
        plenary = PlenaryPersonality(existing[0])
        pdir = os.path.join(self.config.get("broker", "plenarydir"), archetype)
        plenary.remove(pdir)
        
        session.delete(existing[0]);
        session.flush();
        return




#if __name__=='__main__':
