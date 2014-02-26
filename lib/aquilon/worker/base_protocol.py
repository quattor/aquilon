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

class AnonymousRequest(server.Request):

    def getPrincipal(self):
        """For any anonymous channel, always returns None."""
        return None

class AnonymousSite(server.Site):
    """
    Overrides the basic HTTPChannel protocol with AnonHTTPChannel to
    provide a getPrincipal method.  Should be kept consistent with
    any other changes from kncwrappers.
    """
    requestFactory = AnonymousRequest

    # Overriding http.HTTPFactory's log() for consistency with KNCSite.
    # This is exactly the default server.Site.log() method for now.
    def log(self, request):
        if hasattr(self, "logFile"):
            line = '%s - %s %s "%s" %d %s "%s" "%s"\n' % (
                request.getClientIP(),
                # request.getUser() or "-", # the remote user is almost never important
                "-",
                self._logDateTime,
                '%s %s %s' % (self._escape(request.method),
                              self._escape(request.uri),
                              self._escape(request.clientproto)),
                request.code,
                request.sentLength or "-",
                self._escape(request.getHeader("referer") or "-"),
                self._escape(request.getHeader("user-agent") or "-"))
            self.logFile.write(line)
