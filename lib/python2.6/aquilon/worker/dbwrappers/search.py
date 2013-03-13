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
"""Provides the logic used by all the search_next commands."""


import re

from aquilon.utils import force_int

int_re = re.compile(r'^(\d+)')


def search_next(session, cls, attr, value, start, pack, **filters):
    q = session.query(cls).filter(attr.startswith(value))
    if filters:
        q = q.filter_by(**filters)
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
