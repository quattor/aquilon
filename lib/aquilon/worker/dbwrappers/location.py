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
"""Wrapper to make getting a location simpler."""


from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.model import Location


def get_location(session, query_options=None, **kwargs):
    """Somewhat sophisticated getter for any of the location types."""
    cls = None
    name = None
    for key, mapper in Location.__mapper__.polymorphic_map.items():
        if key == "company":
            # temporary until locations in DB restructured
            value = kwargs.get("organization", None)
        else:
            value = kwargs.get(key, None)

        if value is None:
            continue

        if cls:  # pragma: no cover
            raise ArgumentError("Please specify just a single location "
                                "parameter.")
        name = value
        cls = mapper.class_

    if not cls:
        return None

    try:
        q = session.query(cls)
        q = q.filter_by(name=name)
        if query_options:
            q = q.options(query_options)
        dblocation = q.one()
    except NoResultFound:
        raise NotFoundException("%s %s not found." %
                                (cls._get_class_label(), name))
    except MultipleResultsFound:  # pragma: no cover
        raise ArgumentError("There are multiple matches for %s %s." %
                            (cls._get_class_label(), name))
    return dblocation


def add_location(session, cls, name, parent, **kwargs):
    cls.get_unique(session, name, preclude=True)
    dbloc = cls(name=name, parent=parent, **kwargs)
    session.add(dbloc)
    return dbloc
