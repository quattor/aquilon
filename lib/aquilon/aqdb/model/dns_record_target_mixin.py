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
""" Mixin class for DnsRecord with target """

from sqlalchemy.orm import object_session, validates
from aquilon.exceptions_ import ArgumentError


class DnsRecordTargetMixin(object):

    @validates('target')
    def validate_target(self, key, target):  # pylint: disable=W0613
        if not target:
            raise ValueError("target cannot be empty")

        session = object_session(target)
        with session.no_autoflush:
            grn = self.dependent_grn
            if grn:
                self.check_target_conflict(grn, target.dns_records)

        return target

    def check_grn_conflict(self, grn):
        for rec in self.target.dns_records:
            try:
                rec.check_grn_conflict(grn)
            except ArgumentError as e:
                raise ArgumentError("{0} depends on {1}. It conflicts "
                                    "with {2}: {3}"
                                    .format(self, rec, grn, e))

    def check_target_conflict(self, grn, dns_records):
        for rec in dns_records:
            try:
                rec.check_grn_conflict(grn)
            except ArgumentError as e:
                raise ArgumentError("{0} is assoicated with {1}. It conflicts "
                                    "with target {2}: {3}"
                                    .format(self, grn, rec, e))
