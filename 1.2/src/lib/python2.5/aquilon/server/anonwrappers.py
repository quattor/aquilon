#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''If you can read this, you should be Documenting'''

from twisted.web import server, http
from twisted.python import log

class AnonHTTPChannel(http.HTTPChannel):
    """
    This adds getPrinciple() to the base channel.  Since there is no
    knc in use here, it just returns None.
    """

    def getPrinciple(self):
        """For any anonymous channel, always returns None."""
        return None


class AnonSite(server.Site):
    """
    Overrides the basic HTTPChannel protocol with AnonHTTPChannel to
    provide a getPrinciple method.  Should be kept consistent with
    any other changes from kncwrappers.
    """
    protocol = AnonHTTPChannel

    # Overriding http.HTTPFactory's log() for consistency with KNCSite.
    # This is exactly the default server.Site.log() method for now.
    def log(self, request):
        if hasattr(self, "logFile"):
            line = '%s - %s %s "%s" %d %s "%s" "%s"\n' % (
                request.getClientIP(),
                # request.getUser() or "-", # the remote user is almost never important
                "-",
                http._logDateTime,
                '%s %s %s' % (self._escape(request.method),
                              self._escape(request.uri),
                              self._escape(request.clientproto)),
                request.code,
                request.sentLength or "-",
                self._escape(request.getHeader("referer") or "-"),
                self._escape(request.getHeader("user-agent") or "-"))
            self.logFile.write(line)

