# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrappers for using knc with the stock twisted server implementations."""


from twisted.web import server, http
from twisted.python import log


class KNCHTTPChannel(http.HTTPChannel):
    """
    Normal usage for the server is to be given data over a
    socket by knc.  The few lines of that data are extra info
    about the connection.  This needs to be stripped
    (and saved), which is all this does.
    """

    def __init__(self, *args, **kwargs):
        self.__needKNCInfo = 1
        self.kncinfo = {}
        http.HTTPChannel.__init__(self, *args, **kwargs)

    # FIXME: Should probably throw some sort of error if the line
    # does not follow the expected format.
    # This is odd since http is using \r\n but knc is just using \n...
    # We essentially get all the knc info *and* the first line of client
    # info in the "first line".
    def lineReceived(self, line):
        if self.__needKNCInfo:
            self.resetTimeout()
            lines = line.split("\n")
            if len(lines) > 1:
                for l in lines:
                    self.lineReceived(l)
                return
            if line == 'END':
                self.__needKNCInfo = 0
                #log.msg("Finished receiving knc info.")
                return
            (key, value) = line.split(':', 1)
            #log.msg("Got knc info key='%s' value='%s'" % (key, value))
            self.kncinfo[key] = value
            return
        http.HTTPChannel.lineReceived(self, line)

    def getPrincipal(self):
        return self.kncinfo.get("CREDS")

    # FIXME: Generally, twisted methods would return an IPv4Address here.
    def getClientIP(self):
        """The Request object would normally supply this method.  
        However, the client IP is being obtained via knc.  Ideally this
        subclass could just override the Request object creation and
        give it this info, but that does not seem to be straightforward.

        """
        return self.kncinfo.get("REMOTE_IP")
            

class KNCSite(server.Site):
    protocol = KNCHTTPChannel

    # Overriding http.HTTPFactory's log() to use some knc info instead
    # of ignoring it (which is almost funny, as the line to print
    # getUser() is commented out... could have just fiddled with that).
    # Also made "IP address" return the value given from knc, instead
    # of "None" (since, as far as the framework is concerned, the
    # connection came in over a unix domain socket and not tcp/ip).
    def log(self, request):
        if hasattr(self, "logFile"):
            line = '%s - %s %s "%s" %d %s "%s" "%s"\n' % (
                #request.getClientIP(),
                request.channel.getClientIP(),
                # request.getUser() or "-", # the remote user is almost never important
                request.channel.getPrincipal(),
                http._logDateTime,
                '%s %s %s' % (self._escape(request.method),
                              self._escape(request.uri),
                              self._escape(request.clientproto)),
                request.code,
                request.sentLength or "-",
                self._escape(request.getHeader("referer") or "-"),
                self._escape(request.getHeader("user-agent") or "-"))
            self.logFile.write(line)


