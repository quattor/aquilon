# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# See LICENSE for copying information.
#
# This module is part of Aquilon

from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.cfg import Personality
from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.cfg.tld import Tld
from aquilon.aqdb.cfg.cfg_path import CfgPath
import re

class CommandAddOS(BrokerCommand):

    required_parameters = [ "os", "vers", "archetype" ]

    def render(self, session, os, vers, archetype, **arguments):
        valid = re.compile('^[a-zA-Z0-9_.-]+$')
        if (not valid.match(os)):
            raise ArgumentError("OS name '%s' is not valid" % os)
        if not valid.match(vers):
            raise ArgumentError("OS version '%s' is not valid" % vers)

        path = os + "/" + vers

        dbtld = session.query(Tld).filter_by(type='os').first()
        existing = session.query(CfgPath).filter_by(relative_path=path, tld=dbtld).first()

        if existing:
            raise ArgumentError("OS version '%s' already exists" % path)

        dbos = CfgPath(tld=dbtld, relative_path=path)

        session.save(dbos)
        return
