# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Contains the logic for `aq add location`."""


from sqlalchemy.orm.exc import NoResultFound

from aquilon import const
from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import (Location, Company, Hub, Continent, Country,
                                Campus, City, Building, Room, Rack, Desk)

# FIXME: This probably belongs in location.py
# It's also broken, as campus is not strictly between country and city.
# The list of imports above needs to include all of these entries.
const.location_types = ("company", "hub", "continent", "country", "campus",
                        "city", "building", "room", "rack", "desk")

def add_location(session, name, fullname, type, parent_name, parent_type,
                 comments=None, address=None):
    """ Perform all the initialization and error checking to add a location

        Returns a new location which has not been added to any session, allows
        code reuse while also being able to run DSDB commands before commiting
        the transactions
    """
    loc = Location.get_unique(session, name=name,
                              location_type=type, preclude=True)

    parent = Location.get_unique(session, name=parent_name,
                                 location_type=parent_type, compel=True)

    type_weight = const.location_types.index(type)
    parent_weight = const.location_types.index(parent_type)

    if type_weight <= parent_weight:
        raise ArgumentError("Type %s cannot be a parent of %s." %
                    (parent_type.capitalize(), type.capitalize()))

    location_type = globals()[type.capitalize()]
    if not issubclass(location_type, Location):
        raise ArgumentError("%s is not a known location type." % (
            type.capitalize()))

    if not fullname:
        fullname = name

    kw={'name': name, 'fullname': fullname, 'parent': parent,
        'comments': comments}

    if type == 'building':
        kw['address'] = address

    return location_type(**kw)

class CommandAddLocation(BrokerCommand):

    required_parameters = ["name", "fullname", "type", "parentname",
                           "parenttype", "comments"]

    def render(self, session, name, fullname, type,
            parentname, parenttype, comments, **arguments):

        session.add(add_location(session, name, fullname, type, parentname,
                                 parenttype, comments))
        return
