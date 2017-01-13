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
"""Review formatter."""

from aquilon.aqdb.model import Review
from aquilon.worker.formats.formatters import ObjectFormatter

_testing_status = {
    None: 'Untested',
    True: 'Success',
    False: 'Failed',
}

_approval_status = {
    None: 'No decision',
    True: 'Approved',
    False: 'Denied',
}


class ReviewFormatter(ObjectFormatter):
    def format_raw(self, review, indent="", embedded=True, indirect_attrs=True):
        details = [indent + "Review request"]
        details.append(indent + "  Target {0:c}: {0.name}".format(review.target))
        details.append(indent + "  Source {0:c}: {0.name}".format(review.source))
        details.append(indent + "    Commit ID: %s" % review.commit_id)
        details.append(indent + "  Testing status: %s" %
                       _testing_status[review.tested])
        if review.testing_url:
            details.append(indent + "  Testing URL: %s" % review.testing_url)
        if review.review_url:
            details.append(indent + "  Code Review URL: %s" % review.review_url)
        details.append(indent + "  Approval status: %s" %
                       _approval_status[review.approved])

        return "\n".join(details)

    def csv_fields(self, review):
        yield (review.target,
               review.source,
               review.commit_id,
               review.review_url or "",
               review.testing_url or "",
               review.tested if review.tested is not None else "",
               review.approved if review.approved is not None else "")

ObjectFormatter.handlers[Review] = ReviewFormatter()
