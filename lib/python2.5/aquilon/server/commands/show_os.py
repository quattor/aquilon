# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# See LICENSE for copying information
#
# This module is part of Aquilon


from aquilon.server.broker import BrokerCommand
from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import CfgPath, Tld


class CommandShowOS(BrokerCommand):

    def render(self, session, os, vers, archetype, **arguments):
        dbtld = session.query(Tld).filter_by(type="os").first()
        q = session.query(CfgPath).filter_by(tld=dbtld)
        if vers and os:
            q = q.filter_by(relative_path=os + '/' + vers)
        elif os:
            q = q.filter(CfgPath.relative_path.like(os + '/%'))
        elif vers:
            q = q.filter(CfgPath.relative_path.like('%/' + vers))
        oslist = q.all()
        if not oslist:
            raise NotFoundException("No matching operating system")
        return oslist


