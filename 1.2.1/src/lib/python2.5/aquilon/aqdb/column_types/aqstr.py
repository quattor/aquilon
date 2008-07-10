#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" If you can read this you should be documenting """
import sqlalchemy.types as types

class AqStr(types.TypeDecorator):
    """a type that decorates String, normalizes case to lower and strips
        leading and trailing whitespace """

    impl = types.String

    def process_bind_param(self, value, engine):
        return value.strip().lower()

    def process_result_value(self, value, engine):
        return value

    def copy(self):
        return AqStr(self.impl.length)
