# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a service instance simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.svc.service_instance import ServiceInstance
from aquilon.aqdb.sy.build_item import BuildItem


def get_service_instance(session, dbservice, instance):
    try:
        dbsi = session.query(ServiceInstance).filter_by(
                service=dbservice, name=instance).one()
    except InvalidRequestError, e:
        raise NotFoundException("Service %s instance %s not found (try `aq add service --service %s --instance %s` to add it)"
                % (dbservice.name, instance, dbservice.name, instance))
    return dbsi

def get_client_service_instances(session, dbclient):
    service_instances = []
    builditems = session.query(BuildItem).filter_by(host=dbclient).all()
    service_instances = [bi.cfg_path.svc_inst for bi in builditems]
    return service_instances


