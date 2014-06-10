# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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

import re

_unpadded_re = re.compile(r'\b([0-9a-f])\b')
_nocolons_re = re.compile(r'^([0-9a-f]{2}){6}$')
_two_re = re.compile(r'[0-9a-f]{2}')
_padded_re = re.compile(r'^([0-9a-f]{2}:){5}([0-9a-f]{2})$')


class MACAddress(object):
    __slots__ = ('address', 'value')

    def __init__(self, address=None, value=None):
        if address is not None:
            if value is None:
                # Strip, lower, and then use a regex for zero-padding if
                # needed...
                address = _unpadded_re.sub(r'0\1', str(address).strip().lower())
                # If we have exactly twelve hex characters, add the colons.
                if _nocolons_re.search(address):
                    address = ":".join(_two_re.findall(address))
                # Check to make sure we're good.
                if not _padded_re.search(address):
                    raise ValueError("Invalid MAC address format.")
                value = long(address.replace(':', ''), 16)
        elif value is None:
            raise ValueError("Must specify either address or value.")
        self.value = value

        # Force __str__() to generate it so we don't depend on the input
        # formatting
        self.address = None

    def __eq__(self, other):
        try:
            return self.value == other.value
        except AttributeError:
            return NotImplemented

    def __ne__(self, other):
        res = self.__eq__(other)
        if res is NotImplemented:
            return res
        return not res

    def __gt__(self, other):
        if not isinstance(other, MACAddress):
            return NotImplemented
        return self.value > other.value

    def __lt__(self, other):
        if not isinstance(other, MACAddress):
            return NotImplemented
        return self.value < other.value

    def __ge__(self, other):
        if not isinstance(other, MACAddress):
            return NotImplemented
        return self.value >= other.value

    def __le__(self, other):
        if not isinstance(other, MACAddress):
            return NotImplemented
        return self.value <= other.value

    def __hash__(self):
        return hash(self.value)

    def __add__(self, other):
        if not isinstance(other, int):
            return NotImplemented
        return MACAddress(value=self.value + other)

    def __sub__(self, other):
        if not isinstance(other, int):
            return NotImplemented
        return MACAddress(value=self.value - other)

    def __str__(self):
        if not self.address:
            addr = "%012x" % self.value
            addr = ":".join(["".join(t) for t in zip(addr[0:len(addr):2],
                                                     addr[1:len(addr):2])])
            self.address = addr
        return self.address

    def __repr__(self):
        return "<MAC %s>" % self


