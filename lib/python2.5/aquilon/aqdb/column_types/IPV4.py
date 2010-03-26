# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
""" Translates dotted quad strings into long integers """

from struct import pack, unpack
from socket import inet_aton, inet_ntoa

import sqlalchemy

def dq_to_int(dq):
        return unpack('!L', inet_aton(dq))[0]

def int_to_dq(n):
    #Force incoming Decimal to a long to prevent odd issues from struct.pack()
    return inet_ntoa(pack('!L', long(n)))

def cidr_to_int(cidr):
    return(0xffffffffL >> (32- cidr)) << (32 - cidr)

def get_bcast(ip, cidr):
    return int_to_dq( dq_to_int(ip) |  (0xffffffff - cidr_to_int(cidr)))

class IPV4(sqlalchemy.types.TypeDecorator):
    """ A type to wrap IP addresses to and from the DB """

    impl = sqlalchemy.types.Integer
    impl.length = 9  # hardcoding for now, TODO: figure it out and fix

    def process_bind_param(self, dq, engine):
        if not dq:
            return None
        #if column is nullable you cant raise TypeError('IPV4 cant be None')

        dq = str(dq)
        q = dq.split('.')

        if len(q) != 4:
            msg = "%r: IPv4 address invalid: should contain 4 bytes" %(dq)
            raise TypeError(msg)

        for x in q:
            if 0 > int(x) > 255:
                msg = (dq, " : bytes should be between 0 and 255")
                raise TypeError(msg)

        return dq_to_int(dq)

    def process_result_value(self, n, engine):
        # Force the incoming Decimal to a long to prevent odd issues when
        # struct.pack() tries it...
        if n is None:
            return None
        return int_to_dq(n)

    def copy(self):
        return IPV4(self.impl.length)

