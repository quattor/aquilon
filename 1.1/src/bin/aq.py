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

import sys, os

BINDIR = os.path.dirname( os.path.realpath(sys.argv[0]) )
sys.path.append( os.path.join( BINDIR, "..", "lib", "python2.5" ) )

import aquilon.client.depends

from twisted.python import log
from twisted.internet import reactor, error
import urllib
from aquilon.client.optparser import OptParser, ParsingError

# Using this for gethostname for now...
import socket

# FIXME: This should probably be broken out into its own file at some
# point.  The tricky part is making sure getPage is picked up correctly.
# The getPage method will need to handle different response types
# correctly, anyway.
class RESTResource(object):
    def __init__(self, uri):
        self.uri = uri
    
    def get(self):
        return self._sendRequest('GET')

    def post(self, **kwargs):
        postData = urllib.urlencode(kwargs)
        mimeType = 'application/x-www-form-urlencoded'
        return self._sendRequest('POST', postData, mimeType)

    def put(self, data, mimeType):
        return self._sendRequest('PUT', data, mimeType)

    def delete(self):
        return self._sendRequest('DELETE')

    def _sendRequest(self, method, data="", mimeType=None):
        headers = {}
        if mimeType:
            headers['Content-Type'] = mimeType
        if data:
            headers['Content-Length'] = str(len(data))
        return getPage(
            self.uri, method=method, postdata=data, headers=headers)

def gotPage(pageData, uri):
    print "Got representation of %s:" % uri
    print pageData

# FIXME: This behavior might be incorrect... might want to exit(1) in some
# situations.
def handleFailure(failure):
    """Final stop handling for all errors - this will return success
    and let the reactor stop cleanly."""
    if failure.check(error.ProcessTerminated):
        print "Communications subprocess terminated:", failure.getErrorMessage()
    else:
        print "Error:", failure.getErrorMessage()

if __name__ == "__main__":
    parser = OptParser( os.path.join( BINDIR, '..', 'etc', 'input.xml' ) )
    try:
        (command, transport, commandOptions, globalOptions) = parser.getOptions()
    except ParsingError, e:
        print '%s: Option parsing error: %s' % (sys.argv[0], e.error)
        print '%s: Try --help for usage details.' % (sys.argv[0])
        sys.exit(1)

    if globalOptions.has_key('debug') and globalOptions['debug']:
        log.startLogging(sys.stderr)

    host = globalOptions.has_key('aqhost') and globalOptions['aqhost'] or socket.gethostname()
    port = globalOptions.has_key('aqport') and globalOptions['aqport'] or "6900"

    if transport is None:
        print >>sys.stderr, "Unimplemented command ", command
        exit(1)

    # Decent amount of magic here...
    # Even though the server connection might be tunneled through
    # knc, the easiest way to consistently address the server is with
    # a URL.  That's the first half.
    # The relative URL defined by tranport.path comes from the xml
    # file used for options definitions.  This is a standard python
    # string formatting, with references to the options that might
    # be given on the command line.
    uri = str( 'http://%s:%s/' % (host, port) + transport.path % commandOptions )

    if globalOptions.has_key('usesock') and globalOptions['usesock']:
        from aquilon.client.socketwrappers import getPage
    elif globalOptions.has_key('noknc') and globalOptions['noknc']:
        from aquilon.client.ncwrappers import getPage
    else:
        from aquilon.client.kncwrappers import getPage

    if transport.method == 'get':
        # All command line options are (hopefully) in the URI already.
        # Hopefully can get away without something like this:
        # uri = uri + '?' + urllib.urlencode(config['parameters'])
        d = RESTResource(uri).get()
    elif transport.method == 'put':
        # FIXME: This will need to be more complicated.
        # In some cases, we may even need to call code here.
        putData = urllib.urlencode(commandOptions)
        mimeType = 'application/x-www-form-urlencoded'
        d = RESTResource(uri).put(putData, mimeType)
    elif transport.method == 'delete':
        # Again, all command line options should be in the URI already.
        d = RESTResource(uri).delete()
    else:
        # FIXME: Need a stanza for POST.
        # d = RESTResource(uri).post(**config['parameters'])
        print >>sys.stderr, "Unhandled transport method ", transport.method
        sys.exit(1)

    d.addCallback(gotPage, uri).addErrback(handleFailure).addCallback(lambda _: reactor.stop())

    #import pdb
    #pdb.set_trace()
    reactor.run()

