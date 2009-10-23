# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
""" This module implements the AqMac column_type. """
import re
import sqlalchemy


from aquilon.exceptions_ import ArgumentError

class AqMac(sqlalchemy.types.TypeDecorator):
    """ A type that decorates MAC address.

        It normalizes case to lower, strips leading and trailing whitespace,
        adds colons, and adds padding zeroes.

        It should always be initialized as AqMac(17).  This accounts for
        six groups of two characters and five colon separators.

        """

    impl = sqlalchemy.types.String

    unpadded_re = re.compile(r'\b([0-9a-f])\b')
    nocolons_re = re.compile(r'^([0-9a-f]{2}){6}$')
    two_re = re.compile(r'[0-9a-f]{2}')
    padded_re = re.compile(r'^([0-9a-f]{2}:){5}([0-9a-f]{2})$')

    def process_bind_param(self, value, engine):
        if value is None:
            return value
        # Strip, lower, and then use a regex for zero-padding if needed...
        value = self.unpadded_re.sub(r'0\1', str(value).strip().lower())
        # If we have exactly twelve hex characters, add the colons.
        if self.nocolons_re.search(value):
            value = ":".join(self.two_re.findall(value))
        # Check to make sure we're good.
        if self.padded_re.search(value):
            return value
        raise ArgumentError("Invalid format '%s' for MAC.  Please use 00:1a:2b:3c:0d:55, 001a2b3c0d55, or 0:1a:2b:3c:d:55" %
                value)

    def process_result_value(self, value, engine):
        return value

    def copy(self):
        return AqMac(self.impl.length)


