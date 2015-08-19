# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
""" Mixin class for DnsRecord with target """

from sqlalchemy.orm import object_session, validates
from aquilon.exceptions_ import ArgumentError

class DnsRecordTargetMixin(object):

    @validates('target')
    def validate_target(self, key, target):
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
