# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
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
