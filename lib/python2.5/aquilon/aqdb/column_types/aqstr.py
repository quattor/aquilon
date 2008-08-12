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
import sys
import os


if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

import sqlalchemy.types as types


class AqStr(types.TypeDecorator):
    """a type that decorates String, normalizes case to lower and strips
        leading and trailing whitespace """

    impl = types.String

    def process_bind_param(self, value, engine):
        return str(value).strip().lower()

    def process_result_value(self, value, engine):
        return value

    def copy(self):
        return AqStr(self.impl.length)
