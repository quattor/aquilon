# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2017  Contributor
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
""" Helper classes for dns testing """

import struct


# Taken from lib/aquilon/worker/formats/dns_record.py
def inaddr_ptr(ip):
    octets = str(ip).split('.')
    octets.reverse()
    return "%s.in-addr.arpa" % '.'.join(octets)


# Taken from lib/aquilon/worker/formats/dns_record.py
def in6addr_ptr(ip):
    octets = list(struct.unpack("B" * 16, ip.packed))
    octets.reverse()
    # This may not look intuitive, but this was the fastest variant I could come
    # up with - improvements are welcome :-)
    return "".join(format((octet & 0xf) << 4 | (octet >> 4), "02x")
                   for octet in octets).replace("", ".")[1:-1] + ".ip6.arpa"

# Taken from lib/aquilon/worker/formats/dns_record.py
def ip6(ip):
    octets = struct.unpack("B" * 16, ip.packed)
    return "\\" + "\\".join(format(octet, "03o") for octet in octets)
