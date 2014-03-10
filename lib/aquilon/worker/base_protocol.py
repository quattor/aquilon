# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Provide an anonymous access channel to the Site."""

from twisted.web import server, http

_next_sequence_no = 0
"""Next request sequence number, see _get_next_sequence_no()"""

def _get_next_sequence_no():
    """Return the next sequence number for an AQDRequest"""
    global _next_sequence_no
    num = _next_sequence_no
    _next_sequence_no += 1
    return num


class AQDRequest(server.Request):
    """
    Overrides the basic Request object to provide a getPrincipal method.
    """

    def __init__(self, *args, **kwargs):
        self.__sequence_no = _get_next_sequence_no()
        server.Request.__init__(self, *args, **kwargs)

    def getPrincipal(self):
        """By default we return None."""
        return None

    @property
    def sequence_no(self):
        return self.__sequence_no


class AQDSite(server.Site):
    """
    Override server.Site to provide a better implemtation of log.
    """
    requestFactory = AQDRequest

    # Overriding http.HTTPFactory's log() to log the username instead
    # of ignoring it (which is almost funny, as the line to print
    # getUser() is commented out... could have just fiddled with that).
    def log(self, request):
        if hasattr(self, "logFile"):
            line = '%s - %s %s "%s" %d %s "%s" "%s"\n' % (
                request.getClientIP(),
                request.getPrincipal() or "-",
                self._logDateTime,
                '%s %s %s' % (self._escape(request.method),
                              self._escape(request.uri),
                              self._escape(request.clientproto)),
                request.code,
                request.sentLength or "-",
                self._escape(request.getHeader("referer") or "-"),
                self._escape(request.getHeader("user-agent") or "-"))
            self.logFile.write(line)
