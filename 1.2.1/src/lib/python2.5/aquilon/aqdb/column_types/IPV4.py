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


import struct
from socket import inet_aton, inet_ntoa, error as socket_error
from exceptions import TypeError
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

import sqlalchemy.types as types


class IPv4AddrTypeError(TypeError):
    def __init__(self, addr):
        self.addr = addr
    def __str__(self):
        return "Illegal IPv4 address '%s'" % self.addr

class IPV4(types.TypeDecorator):
    """ A type to wrap IP addresses to and from the DB """
    def process_bind_param(self,value,engine):
        try:
            return super(IPV4,self).convert_bind_param(
                struct.unpack('!L',inet_aton(value))[0],engine)
        except socket_error:
            raise IPv4AddrTypeError(value)

    # from the database
    def process_result_value(self,value,engine):
        return inet_ntoa(
            struct.pack('!L',super(
                IPV4,self).convert_result_value(value,engine)))

    def copy(self):
        return AqStr(self.impl.length)


#TEST ME!!!: create a tiny table, insert valid, and invalid types. delete table
