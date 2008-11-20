#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del model`."""


from sqlalchemy.exceptions import InvalidRequestError
from twisted.python import log

from aquilon.exceptions_ import NotFoundException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.vendor import get_vendor
from aquilon.aqdb.hw.model import Model


class CommandDelModel(BrokerCommand):

    required_parameters = ["name", "vendor", "type"]

    def render(self, session, name, vendor, type, **arguments):
        dbvendor = get_vendor(session, vendor)
        try:
            dbmodel = session.query(Model).filter_by(name=name,
                    vendor=dbvendor, machine_type=type).one()
        except InvalidRequestError, e:
            raise NotFoundException("Model '%s' with vendor %s and type %s not found: %s"
                    % (name, vendor, type, e))
        if dbmodel.machine_specs:
            # FIXME: Log some details...
            log.msg("Before deleting model %s %s '%s', removing machine specifications." % (type, vendor, name))
            session.delete(dbmodel.machine_specs)
        session.delete(dbmodel)
        return


#if __name__=='__main__':
