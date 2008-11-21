# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a model simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.hw.model import Model


def get_model(session, model):
    try:
        dbmodel = session.query(Model).filter_by(name=model).one()
    except InvalidRequestError, e:
        raise NotFoundException("Model %s not found: %s" % (model, e))
    return dbmodel


