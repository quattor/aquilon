# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Wrappers for using knc with the stock twisted server implementations."""

from twisted.web import http
from aquilon.worker.base_protocol import AQDRequest, AQDSite

import logging
from aquilon.utils import force_ascii, force_ipv4

LOGGER = logging.getLogger(__name__)


class KNCRequest(AQDRequest):

    def getPrincipal(self):
        return self.channel.kncinfo.get("CREDS")

    def getClientIP(self):
        """The Request object would normally supply this method.
        However, the client IP is being obtained via knc.
        """
        return self.channel.kncinfo.get("REMOTE_IP")


class KNCProtocolException(Exception):
    pass


class KNCHTTPChannel(http.HTTPChannel):
    """
    The KNC HTTP Channel is passed data over a socket by KNC.  The first
    few lines of data contain extra information about the connection.
    We take these data and stash them into the KNC Request.
    """
    __KNC_fields = {
        'CREDS': force_ascii,
        'REMOTE_IP': force_ipv4
    }

    def __init__(self, *args, **kwargs):
        self.__need_knc_data = 1
        self.logger = LOGGER
        self.kncinfo = {}
        http.HTTPChannel.__init__(self, *args, **kwargs)

    def kncLineReceived(self, data):
        # KNC uses '\n' to delimit lines, while HTTP uses '\n\r', therefore
        # all of the KNC data comes on the first line.  Split these up
        # and process them speratly.
        lines = data.split('\n')
        for line in lines:
            if not self.__need_knc_data:
                # Pass remaining data through the the HTTP Channel
                http.HTTPChannel.lineReceived(self, line)
            elif line == 'END':
                # Check that we have now recieved all of the metadata
                # that we are expecting...
                for field, checker in self.__KNC_fields.iteritems():
                    if field not in self.kncinfo:
                        raise KNCProtocolException('Missing %s' % field)
                self.__need_knc_data = 0
            else:
                if not line:
                    raise KNCProtocolException('Malformed KNC request')
                if ':' not in line:
                    raise KNCProtocolException('Malformed KNC metatdata')
                (key, value) = line.split(':', 1)
                if not key:
                    raise KNCProtocolException('KNC Metadata key missing')
                if not value:
                    raise KNCProtocolException('KNC Metadata value missing')
                if key in self.__KNC_fields:
                    try:
                        self.kncinfo[key] = self.__KNC_fields[key](key, value)
                    except ArgumentError, e:
                        raise KNCProtocolException(e.message)

    def lineReceived(self, line):
        if self.__need_knc_data:
            self.resetTimeout()
            try:
                self.kncLineReceived(line)
            except KNCProtocolException, e:
                self.logger.warning("Closed KNC Connection: %s" % e.message)
                self.transport.write("HTTP/1.1 400 Bad KNC Request\r\n\r\n")
                self.transport.loseConnection()
        else:
            http.HTTPChannel.lineReceived(self, line)


class KNCSite(AQDSite):
    requestFactory = KNCRequest
    protocol = KNCHTTPChannel
