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

from sqlalchemy.orm.attributes import set_committed_value

from aquilon.worker.dbwrappers.resources import get_resource_holder


def show_resource(session, logger, hostname, cluster, metacluster,
                  resourcegroup, all, name, resource_class):
    q = session.query(resource_class)
    if name:
        q = q.filter_by(name=name)
    if hostname or cluster or resourcegroup:
        who = get_resource_holder(session, logger, hostname, cluster,
                                  metacluster, resourcegroup)
        q = q.filter_by(holder=who)
    else:
        who = None

    results = q.all()
    if who:
        for dbresource in results:
            set_committed_value(dbresource, 'holder', who)

    return results
