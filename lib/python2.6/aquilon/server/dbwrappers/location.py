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
"""Wrapper to make getting a location simpler."""


from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from aquilon import const
from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.model import Location


def get_location(session, **kwargs):
    """Somewhat sophisticated getter for any of the location types."""
    location_type = None # The type in the DB
    argname = None # The name of the key in the args
    #TODO: remove dependency on const and pull types from an ordered query
    for lt in const.location_types:
        lookup = lt
        if lt == "company":
            lookup = "organization" # temporary until locations in DB restructured
        if kwargs.get(lookup):
            if location_type:
                raise ArgumentError("Single location can not be both %s and %s."
                        % (lookup, location_type))
            location_type = lt
            argname = lookup
    if not location_type:
        return None
    try:
        dblocation = session.query(Location).filter_by(
                name=kwargs[argname], location_type=location_type).one()
    except NoResultFound:
        raise NotFoundException("%s %s not found." %
                                (location_type.capitalize(),
                                 kwargs[location_type]))
    except MultipleResultsFound:
        raise ArgumentError("There are multiple matches for %s %s." %
                            (location_type.capitalize(),
                             kwargs[location_type]))
    return dblocation
