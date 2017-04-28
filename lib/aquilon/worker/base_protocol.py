# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2017  Contributor
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

from six import text_type
from twisted.web import server

from aquilon.worker.logger import RequestLogger
from aquilon.worker.messages import StatusCatalog


_next_sequence_no = 0
"""Next request sequence number, see _get_next_sequence_no()"""

catalog = StatusCatalog()


def _get_next_sequence_no():
    """Return the next sequence number for an AQDRequest"""
    global _next_sequence_no
    num = _next_sequence_no
    _next_sequence_no += 1
    return num


def alt_repr(s):
    # Small helper borrowed from twisted: a version of repr() which always uses
    # double quotes
    r = repr(s)
    if not isinstance(r, text_type):
        r = r.decode("ascii")
    if r.startswith(u"b"):
        r = r[1:]
    if r.startswith(u"'"):
        return r[1:-1].replace(u'"', u'\\"').replace(u"\\'", u"'")
    return r[1:-1]


class AQDRequest(server.Request):
    """
    Overrides the basic Request object to provide a getPrincipal method.
    """

    def __init__(self, *args, **kwargs):
        server.Request.__init__(self, *args, **kwargs)
        self.__sequence_no = _get_next_sequence_no()
        self.status = catalog.create_request_status(auditid=self.__sequence_no)
        self.logger = RequestLogger(self.status)

        d = self.notifyFinish()
        d.addBoth(self.cleanup)

    def getPrincipal(self):
        """By default we return None."""
        return None

    @property
    def sequence_no(self):
        return self.__sequence_no

    def cleanup(self, result):
        if self.logger:
            self.logger.debug("Server finishing request.")
            self.logger.close_handlers()
            self.logger = None

        if self.status:
            catalog.remove_request_status(self.status)
            self.status = None

        # Pass through
        return result

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
                '%s %s %s' % (alt_repr(request.method),
                              alt_repr(request.uri),
                              alt_repr(request.clientproto)),
                request.code,
                request.sentLength or "-",
                alt_repr(request.getHeader("referer") or "-"),
                alt_repr(request.getHeader("user-agent") or "-"))
            self.logFile.write(line)
