# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Wrapper to make getting a network type simpler."""


from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql import and_, update

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.model import Network, AddressAssignment, ARecord


def get_network_byname(session, netname, environment):
    try:
        q = session.query(Network)
        q = q.filter_by(network_environment=environment)
        q = q.filter_by(name=netname)
        dbnetwork = q.one()
    except NoResultFound:
        raise NotFoundException("Network %s not found." % netname)
    # FIXME: network names should be unique
    except MultipleResultsFound:
        raise ArgumentError("There are multiple networks with name %s." %
                            netname)
    return dbnetwork


def get_network_byip(session, ipaddr, environment):
    try:
        q = session.query(Network)
        q = q.filter_by(network_environment=environment)
        q = q.filter_by(ip=ipaddr)
        dbnetwork = q.one()
    except NoResultFound:
        raise NotFoundException("Network with address %s not found." % ipaddr)
    return dbnetwork


def fix_foreign_links(session, oldnet, newnet):
    """
    Fix foreign keys that point to the network table

    When a network is split or multiple networks are merged, foreign keys
    must be updated accordingly. Do not use the size of the old network,
    as it has already been updated when this function gets called.
    """
    session.execute(
        update(AddressAssignment.__table__,
               values={'network_id': newnet.id})
        .where(and_(AddressAssignment.network_id == oldnet.id,
                    AddressAssignment.ip >= newnet.ip,
                    AddressAssignment.ip <= newnet.broadcast))
    )
    session.expire(oldnet, ['assignments'])
    session.expire(newnet, ['assignments'])

    session.execute(
        update(ARecord.__table__,
               values={'network_id': newnet.id})
        .where(and_(ARecord.network_id == oldnet.id,
                    ARecord.ip >= newnet.ip,
                    ARecord.ip <= newnet.broadcast))
    )
    session.expire(oldnet, ['dns_records'])
    session.expire(newnet, ['dns_records'])
