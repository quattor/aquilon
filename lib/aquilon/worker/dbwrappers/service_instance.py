# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Wrapper to make getting a service instance simpler."""

from operator import attrgetter

from sqlalchemy.orm.exc import NoResultFound

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.model import ServiceInstance


def get_service_instance(session, dbservice, instance):
    try:
        dbsi = session.query(ServiceInstance).filter_by(
                service=dbservice, name=instance).one()
    except NoResultFound:
        raise NotFoundException("Service %s, instance %s not found.  Try `aq "
                                "add service --service %s --instance %s` to "
                                "add it." % (dbservice.name, instance,
                                             dbservice.name, instance))
    return dbsi


def check_no_provided_service(dbobject):
    if dbobject.services_provided:
        # De-duplicate and sort the provided service instances
        instances = set([srv.service_instance for srv in
                         dbobject.services_provided])
        instances = sorted(instances, key=attrgetter("service.name", "name"))

        msg = ", ".join(["%s/%s" % (si.service.name, si.name)
                         for si in instances])
        raise ArgumentError("{0} still provides the following services, "
                            "and cannot be deleted: {1!s}."
                            .format(dbobject, msg))
