#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show manager --all`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.formats.system import SimpleSystemList
from aquilon.aqdb.sy.manager import Manager


class CommandShowManagerAll(BrokerCommand):

    def render(self, session, **arguments):
        return SimpleSystemList(session.query(Manager).all())


#if __name__=='__main__':
