#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a service instance simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.service import ServiceInstance, HostList, ServiceMap


def get_service_instance(session, dbservice, instance):
    try:
        dbhl = session.query(HostList).filter_by(name=instance).one()
    except InvalidRequestError, e:
        raise NotFoundException("HostList %s not found (try `aq add service --service %s --instance %s` to add it): %s"
                % (instance, dbservice.name, instance, e))
    try:
        dbsi = session.query(ServiceInstance).filter_by(
                service=dbservice, host_list=dbhl).one()
    except InvalidRequestError, e:
        raise NotFoundException("Service %s instance %s not found (try `aq add service --service %s --instance %s` to add it)"
                % (dbservice.name, instance, dbservice.name, instance))
    return dbsi

# Modeled after get_server_for in aqdb/population_scripts.py
def choose_service_instance(session, dbhost, dbservice):
    # FIXME: The database will support multiple algorithms...
    locations = [dbhost.location]
    while locations[-1].parent is not None:
        locations.append(locations[-1].parent)
    for location in locations:
        maps = session.query(ServiceMap).filter_by(
                location=location).join('service_instance').filter_by(
                service=dbservice).all()
        if len(maps) == 1:
            return maps[0].service_instance
        if len(maps) > 1:
            return self._choose_least_loaded(maps)
    raise ArgumentError("Could not find a relevant service map for service %s on host %s" %
            (dbservice.name, dbhost.fqdn))

# Modeled after least_loaded in aqdb/population_scripts.py
def choose_least_loaded(session, dbmaps):
    least_clients = None
    least_loaded = None
    for map in dbmaps:
        client_count = map.service_instance.client_count
        if not least_loaded or client_count < least_clients:
            least_clients = client_count
            least_loaded = map.service_instance
    return least_loaded


#if __name__=='__main__':
