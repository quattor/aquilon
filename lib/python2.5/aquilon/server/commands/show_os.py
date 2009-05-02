# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# See LICENSE for copying information
#
# This module is part of Aquilon


from aquilon.server.broker import BrokerCommand
from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.cfg.cfg_path import CfgPath
from aquilon.aqdb.cfg.tld import Tld

class CommandShowOsAll(BrokerCommand):

    def render(self, session, os, vers, archetype, **arguments):
        dbtld = session.query(Tld).filter_by(type="os").first()
        if vers and os:
            oslist = session.query(CfgPath).filter_by(relative_path = os+'/'+vers, tld=dbtld).all()
        elif os:
            oslist = session.query(CfgPath).filter(CfgPath.relative_path.like(os+'/%')).filter_by(tld=dbtld).all()
        else:
            oslist = session.query(CfgPath).filter_by(tld=dbtld).all()
    
        if not oslist:
            raise ArgumentError("No matching operating system")
        return oslist
