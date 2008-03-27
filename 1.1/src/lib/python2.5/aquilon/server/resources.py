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

from twisted.application import internet
from twisted.web import server, resource, http
from twisted.internet import defer, utils
from twisted.python import log

from aquilon.server.exceptions_ import AuthorizationException

class ResponsePage(resource.Resource):
    def __init__(self, dbbroker, azbroker, path):
        self.path = path
        self.dbbroker = dbbroker
        self.azbroker = azbroker
        resource.Resource.__init__(self)

    def render(self, request):
        """This is just the default implementation from resource.Resource
        that checks for the appropriate method to delegate to.  This can
        be expanded out to do any default/incoming processing...

        """
        m = getattr(self, 'render_' + request.method, None)
        if not m:
            raise server.UnsupportedMethod(getattr(self, 'allowedMethods', ()))
        return m(request)

    # All of these wrap* functions should probably be elsewhere, and
    # change depending on what should go back to the client.
    def wrapRowsInTable(self, rp):
        retval = []
        if ( rp is None ):
            return "<p>No results.</p>"
        for row in rp:
            data = [ "<td>%s</td>" % elem for elem in row ]
            retval.append( "<tr>\n" + "\n".join(data) + "\n</tr>\n" )
        retstr = "<table>\n" + "\n".join(retval) + "\n</table>\n"
        return str(retstr)

    # This is the wrong spot for this - but where should it go?  Should
    # it be in one of the Host* classes, which is then inherited by the
    # other?
    def wrapHostInTable(self, rp):
        print "Attempting results"
        retval = []
        if ( rp is None ):
            return "<p>No results.</p>"
        for h in rp:
            data = "<td>%s</td><td>%s</td>" % (h.id, h.name)
            retval.append( "<tr>\n" + data + "\n</tr>\n" )
        retstr = "<table>\n" + "\n".join(retval) + "\n</table>\n"
        print "returning ", retstr
        return str(retstr)

    # This is the wrong spot for this - but where should it go?
    def wrapAqdbTypeInTable(self, rp):
        print "Attempting results"
        retval = []
        if ( rp is None ):
            return "<p>No results.</p>"
        for o in rp:
            data = "<td>%s</td><td>%s</td>" % (o.id, o.type)
            retval.append( "<tr>\n" + data + "\n</tr>\n" )
        retstr = "<table>\n" + "\n".join(retval) + "\n</table>\n"
        print "returning ", retstr
        return str(retstr)

    # This is the wrong spot for this - but where should it go?
    def wrapLocationInTable(self, rp):
        print "Attempting results"
        retval = []
        if ( rp is None ):
            return "<p>No results.</p>"
        for loc in rp:
            data = "<td>%s</td><td>%s</td>" % (loc.id, loc.name)
            retval.append( "<tr>\n" + data + "\n</tr>\n" )
        retstr = "<table>\n" + "\n".join(retval) + "\n</table>\n"
        print "returning ", retstr
        return str(retstr)

    def wrapTableInBody(self, result):
        retval = """
        <html>
        <head><title>%s</title></head>
        <body>
        %s
        </body>
        </html>
        """ % (self.path, result)
        return str(retval)

    def finishRender(self, result, request):
        #print "about to write ", result
        request.setHeader('content-length', str(len(result)))
        request.write(result)
        request.finish()
        #print "All done"
        return

    def finishOK(self, result, request):
        """Ignore any results - usually empty for this - and finish"""
        # FIXME: Hack to get around client not understanding
        # zero-length response... Use explicit 0 when knc 1.3 exists.
        # Tried setting it explicitly...
        request.setHeader('content-length', 0)
        # Tried sending a "no content" response...
        #request.setResponseCode( http.NO_CONTENT )
        # For now, just send OK.
        #retval = "OK"
        #request.setHeader('content-length', len(retval))
        #request.write(retval)
        request.finish()
        return

    # TODO: Something should go into both the logs and back to the client...
    def wrapError(self, failure, request):
        # FIXME: This should be overridden, looking for and trapping specific
        # exceptions.  Maybe this is left as a final check.
        print failure.getErrorMessage()
        failure.printDetailedTraceback()
        request.setResponseCode( http.INTERNAL_SERVER_ERROR )
        # FIXME: Ditto from finishOK
        #retval = "FAILED"
        #request.setHeader('content-length', len(retval))
        #request.write(retval)
        request.setHeader('content-length', 0)
        request.finish()
        return failure

    def render_GET(self, request):
        "Accept a GET request"

    def render_PUT(self, request):
        "Accept a PUT request"
        return "Got a PUT request"

    def render_DELETE(self, request):
        "Accept a DELETE request"
        return "Got a DELETE request"

class HostPageContainer(ResponsePage):
    def render_GET(self, request):
        """aqcommand: aq show host --all"""
        #print 'render_GET called'
        try:
            self.azbroker.check(None, request.channel.getPrinciple(), "show",
                                "/host")
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        d = self.dbbroker.showHostAll(session=True)
        d = d.addErrback( self.wrapError, request )
        d = d.addCallback( self.wrapHostInTable )
        d = d.addCallback( self.wrapTableInBody )
        d = d.addCallback( self.finishRender, request )
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET
    
    def getChild(self, path, request):
        "Return the correct HostPage for this path"
        return HostPage(self.dbbroker, self.azbroker, path)

class HostPage(ResponsePage):
    def render_POST(self, request):
        "accept a POST request to add a new host"

    def render_GET(self, request):
        """aqcommand: aq show host --hostname=<host>"""
        #print 'render_GET called'
        #name = request.args['name'][0]
        name = self.path

        try:
            self.azbroker.check(None, request.channel.getPrinciple(), "show",
                                "/host/%s" % name)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        d = self.dbbroker.showHost(name, session=True)
        d = d.addErrback( self.wrapError, request )
        d = d.addCallback( self.wrapHostInTable )
        d = d.addCallback( self.wrapTableInBody )
        d = d.addCallback( self.finishRender, request )
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET

    def render_PUT(self, request):
        """aqcommand: aq add host --hostname=<host>"""
        #name = request.args['name'][0]
        #request.content.seek(0)
        name = self.path

        try:
            self.azbroker.check(None, request.channel.getPrinciple(), "add",
                                "/host/%s" % name)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        d = self.dbbroker.addHost(name, session=True)
        # FIXME: Trap specific exceptions (host exists, etc.)
        d = d.addErrback( self.wrapError, request )
        d = d.addCallback( self.wrapHostInTable )
        d = d.addCallback( self.wrapTableInBody )
        d = d.addCallback( self.finishRender, request )
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET

    def render_DELETE(self, request):
        """aqcommand: aq del host --hostname=<host>"""
        name = self.path

        try:
            self.azbroker.check(None, request.channel.getPrinciple(), "del",
                                "/host/%s" % name)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        d = self.dbbroker.delHost(name, session=True)
        # FIXME: Trap specific exceptions (host exists, etc.)
        d = d.addErrback( self.wrapError, request )
        d = d.addCallback( self.finishOK, request )
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET

class LocationTypePageContainer(ResponsePage):
    def render_GET(self, request):
        """aqcommand: aq show location"""
        #print 'render_GET called'
        try:
            self.azbroker.check(None, request.channel.getPrinciple(), "show",
                                "/location")
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        d = self.dbbroker.showLocationType(session=True)
        d = d.addErrback( self.wrapError, request )
        d = d.addCallback( self.wrapAqdbTypeInTable )
        d = d.addCallback( self.wrapTableInBody )
        d = d.addCallback( self.finishRender, request )
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET
    
    def getChild(self, path, request):
        "Return the correct LocationPage for this path"
        # FIXME: Need to pass in the type...
        return LocationPageContainer(self.dbbroker, self.azbroker, path)

class LocationPageContainer(ResponsePage):
    def render_GET(self, request):
        """aqcommand: aq show location --type"""
        #print 'render_GET called'
        type = self.path
        try:
            self.azbroker.check(None, request.channel.getPrinciple(), "show",
                                "/location/%s" % type)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        d = self.dbbroker.showLocation(session=True, type=type)
        d = d.addErrback( self.wrapError, request )
        d = d.addCallback( self.wrapLocationInTable )
        d = d.addCallback( self.wrapTableInBody )
        d = d.addCallback( self.finishRender, request )
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET
    
    def getChild(self, path, request):
        "Return the correct LocationPage for this path"
        return LocationPage(self.dbbroker, self.azbroker, path)

class LocationPage(ResponsePage):
    def render_POST(self, request):
        "accept a POST request to add a new location"

    def render_GET(self, request):
        """aqcommand: aq show location --locationname=<location>"""
        #print 'render_GET called'
        #name = request.args['name'][0]
        name = self.path

        try:
            self.azbroker.check(None, request.channel.getPrinciple(), "show",
                                "/location/%s" % name)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        d = self.dbbroker.showLocation(name, session=True)
        d = d.addErrback( self.wrapError, request )
        d = d.addCallback( self.wrapLocationInTable )
        d = d.addCallback( self.wrapTableInBody )
        d = d.addCallback( self.finishRender, request )
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET

    def render_PUT(self, request):
        """aqcommand: aq add location --locationname=<location>"""
        #name = request.args['name'][0]
        #request.content.seek(0)
        name = self.path

        try:
            self.azbroker.check(None, request.channel.getPrinciple(), "add",
                                "/location/%s" % name)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        d = self.dbbroker.addLocation(name, session=True)
        # FIXME: Trap specific exceptions (location exists, etc.)
        d = d.addErrback( self.wrapError, request )
        d = d.addCallback( self.wrapLocationInTable )
        d = d.addCallback( self.wrapTableInBody )
        d = d.addCallback( self.finishRender, request )
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET

    def render_DELETE(self, request):
        """aqcommand: aq del location --locationname=<location>"""
        name = self.path

        try:
            self.azbroker.check(None, request.channel.getPrinciple(), "del",
                                "/location/%s" % name)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        d = self.dbbroker.delLocation(name, session=True)
        # FIXME: Trap specific exceptions (location exists, etc.)
        d = d.addErrback( self.wrapError, request )
        d = d.addCallback( self.finishOK, request )
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET

class DummyCommand(ResponsePage):
    def cb_command_output(self, (out, err, code)):
        log.msg("echo finished with return code %d" % code)
        # FIXME: do stuff with err and code
        return out

    def cb_command_error(self, (out, err, signalNum)):
        # FIXME: do stuff with err and signalNum
        return out

    def render_GET(self, request):
        d = utils.getProcessOutputAndValue("/bin/echo",
                [ "/bin/env && echo hello && sleep 1 && echo hi; echo bye" ] )
        d = d.addErrback( self.wrapError, request )
        d = d.addCallbacks(self.cb_command_output, self.cb_command_error)
        d = d.addCallback( self.finishRender, request )
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET

class RestServer(ResponsePage):
    """The root resource is used to define the site as a whole.
        It inherits from ResponsePage for requests to /"""
    def __init__(self, dbbroker, azbroker):
        ResponsePage.__init__(self, dbbroker, azbroker, '')
        #self.putChild('host', HostPageContainer(self.dbbroker,
        #                                        self.azbroker,
        #                                        "host"))
        self.putChild('location', LocationTypePageContainer(self.dbbroker,
                                                            self.azbroker,
                                                            "location"))
        self.putChild('dummy_command', DummyCommand(self.dbbroker,
                                                    self.azbroker,
                                                    "dummy_command"))

    #def getChild(self, path, request):
    #    return ResponsePage(self.dbbroker, self.azbroker,
    #                    path or 'UsageResponse')

    def render_GET(self, request):
        """aqcommand: aq status"""

        try:
            self.azbroker.check(None, request.channel.getPrinciple(), "status",
                                "/")
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        return "<html><head><title>Status</title></head><body>OK</body></html>"

