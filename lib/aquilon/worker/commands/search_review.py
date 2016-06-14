# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016  Contributor
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

from sqlalchemy.orm import aliased, contains_eager

from aquilon.aqdb.model import Branch, Domain, Review
from aquilon.worker.broker import BrokerCommand


class CommandSearchReview(BrokerCommand):

    required_parameters = []
    default_style = "csv"

    def render(self, session, source, target, testing_succeeded, untested,
               approved, undecided, testing_url, review_url, **_):
        q = session.query(Review)

        if source:
            dbsource = Branch.get_unique(session, source, compel=True)
            q = q.filter_by(source=dbsource)

        if target:
            dbtarget = Domain.get_unique(session, target, compel=True)
            q = q.filter_by(target=dbtarget)

        if testing_succeeded is not None:
            q = q.filter_by(tested=testing_succeeded)
        elif untested:
            q = q.filter_by(tested=None)

        if approved is not None:
            q = q.filter_by(approved=approved)
        elif undecided:
            q = q.filter_by(approved=None)

        if testing_url:
            q = q.filter_by(testing_url=testing_url)
        elif testing_url == "":
            q = q.filter_by(testing_url=None)

        if review_url:
            q = q.filter_by(review_url=review_url)
        elif review_url == "":
            q = q.filter_by(review_url=None)

        SA = aliased(Branch)
        TA = aliased(Domain)
        q = q.join(SA, Review.source)
        q = q.join(TA, Review.target)
        q = q.options(contains_eager('source', alias=SA),
                      contains_eager('target', alias=TA))
        q = q.order_by(TA.name, SA.name)

        return q.all()
