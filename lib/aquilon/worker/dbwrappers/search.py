# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Provides the logic used by all the search_next commands."""


import re

from aquilon.utils import force_int

int_re = re.compile(r'^(\d+)')


def search_next(session, cls, attr, value, start, pack, locked=False,
                **filters):
    q = session.query(cls).filter(attr.startswith(value))
    if filters:
        q = q.filter_by(**filters)

    # Doing the locking here is not the most efficient as we're potentially
    # locking a lot of rows - but if there's no better object to lock, then we
    # don't have much choice.

    if locked and q.count() == 0:
        # Nothing to lock -- so we'll crudely pick out the first and
        # lock that.
        q2 = session.query(cls).order_by(attr).limit(1)
        if q2.count() == 1:
            attrval = q2.value(attr)

            # This is not particularly pleasant: Oracle won't permit a
            # "FOR UPDATE" query where "ORDER BY" is given (ORA-02014);
            # constructing the allowable version of the query may not be
            # possible with SQLAlchemy.

            q2 = session.query(cls).filter(attr == attrval)
            session.execute(q2.with_for_update())

            # Re-execute the original query: only 1 will get through here
            q = session.query(cls).filter(attr.startswith(value))
            if filters:
                q = q.filter_by(**filters)

        # Else (q2.count == 0): the table is empty, so we'll just head
        # forwards and accept that this may break in that fairly rare
        # (one-off) case;  something may also have raced and removed the
        # first row we picked.

    elif locked:
        # The FOR UPDATE query needs to be executed separately, otherwise it
        # won't see allocations done in a different session
        session.execute(q.with_for_update())

    if start:
        start = force_int("start", start)
    else:
        start = 1

    entries = set()
    for (attrvalue,) in q.values(attr):
        m = int_re.match(attrvalue[len(value):])
        if m:
            n = int(m.group(1))
            # Only remember entries that we care about...
            if n >= start:
                entries.add(n)
    if not entries:
        return start
    entries = sorted(entries)
    if pack:
        expecting = start
        for current in entries:
            if current > expecting:
                return expecting
            expecting += 1
    return entries[-1] + 1
