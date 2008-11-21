# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a service instance simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.svc.service_instance import ServiceInstance
from aquilon.aqdb.svc.service_map import ServiceMap
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

# Modeled after get_server_for in aqdb/population_scripts.py
def choose_service_instance(session, dbhost, dbservice):
    """ This choosed the "closest" service instance, based on the
        known maps.  It is entirely possible that this location
        could have been served by more lightly loaded servers at
        a broader location in the tree - but that information is
        currently ignored.

    """
    # FIXME: The database will support multiple algorithms...
    locations = [dbhost.location]
    while (locations[-1].parent is not None and
            locations[-1].parent != locations[-1]):
        locations.append(locations[-1].parent)
    for location in locations:
        maps = session.query(ServiceMap).filter_by(
                location=location).join('service_instance').filter_by(
                service=dbservice).all()
        if len(maps) == 1:
            return maps[0].service_instance
        if len(maps) > 1:
            return choose_least_loaded(session, maps)
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


