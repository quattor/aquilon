# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# See LICENSE for copying information
#
# This module is part of Aquilon

import os

from aquilon.server.broker import BrokerCommand
from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.cfg.cfg_path import CfgPath
from aquilon.aqdb.cfg.tld import Tld


class CommandDelOS(BrokerCommand):

    required_parameters = ["os", "vers", "archetype"]

    def render(self, session, os, vers, archetype, **arguments):
        dbtld = session.query(Tld).filter_by(type="os").first()
        relative_path = os + "/" + vers
        q = session.query(CfgPath)
        q = q.filter_by(relative_path=relative_path, tld=dbtld)
        existing = q.all()
        if not existing:
            raise NotFoundException("OS version '%s' is unknown" %
                                    relative_path)

        # TODO: Check dependencies

        for tpl in existing:
            session.delete(tpl)
        return


