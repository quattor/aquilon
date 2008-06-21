#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a cfg_path simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.configuration import CfgPath


def get_cfg_path(session, cfg_tld, cfg_path):
    try:
        dbcfg_path = session.query(CfgPath).filter_by(
                relative_path=cfg_path).join('tld').filter_by(
                        type=cfg_tld).one()
    except InvalidRequestError, e:
        raise NotFoundException("%s template %s not found: %s" %
                (cfg_tld, cfg_path, e))
    return dbcfg_path


#if __name__=='__main__':
