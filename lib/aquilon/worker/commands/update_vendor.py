# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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

from aquilon.aqdb.model import Vendor
from aquilon.worker.broker import BrokerCommand


class CommandUpdateVendor(BrokerCommand):

    required_parameters = ["vendor"]

    def render(self, session, vendor, comments, **arguments):
        dbvendor = Vendor.get_unique(session, vendor, compel=True)

        if comments is not None:
            dbvendor.comments = comments

        session.flush()
        return
