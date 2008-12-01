""" Column type to squash trailing/leading whitespace and lower case """
import sqlalchemy


class AqStr(sqlalchemy.types.TypeDecorator):
    """a type that decorates String, normalizes case to lower and strips
        leading and trailing whitespace """

    impl = sqlalchemy.types.String

    def process_bind_param(self, value, engine):
        if value is None:
            return value
        return str(value).strip().lower()

    def process_result_value(self, value, engine):
        return value

    def copy(self):
        return AqStr(self.impl.length)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
