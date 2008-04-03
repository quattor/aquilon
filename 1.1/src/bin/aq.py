#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''Client for accessing aqd.

It uses knc by default for an authenticated connection, but can also
connect directly.

'''

import sys
import os
import urllib
# Using this for gethostname for now...
import socket

BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(os.path.join(BINDIR, "..", "lib", "python2.5"))
import aquilon.client.depends

from twisted.python import log
from twisted.internet import reactor, error, utils, protocol, defer

from aquilon.client.optparser import OptParser, ParsingError

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


class CommandPassThrough(protocol.ProcessProtocol):
    """Simple wrapper for running commands to immediately pass stdout
    and stderr to the console, and callback on the deferred when the
    command has finished.

    """

    def __init__(self, deferred):
        self.deferred = deferred
        self.outReceived = sys.stdout.write
        self.errReceived = sys.stderr.write

    def processEnded(self, reason):
        e = reason.value
        code = e.exitCode
        if e.signal:
            self.deferred.errback(e.signal)
        else:
            self.deferred.callback(code)


def cb_command_response(code):
    if code:
        print >>sys.stderr, "Return code: %d" % code

def cb_command_error(signalNum):
    print >>sys.stderr, "Error running command, received signal %d" % signalNum

def gotPage(pageData, uri, expect, globalOptions):
    if expect == 'command':
        if globalOptions.get("noexec"):
            print pageData
            return
        d = defer.Deferred()
        p = CommandPassThrough(d)
        # FIXME: Does the command transport need to be any more complicated?
        reactor.spawnProcess(p, "/bin/sh", ("/bin/sh", "-c", pageData),
                                os.environ, '.')
        d = d.addCallbacks(cb_command_response, cb_command_error)
        return d
    else:
        print "[OK] %s" % uri
        print pageData


class CustomAction(object):
    """Any custom code that needs to be written to run before contacting
    the server can go here for now.

    Each method should expect to add to the commandOptions object, and
    should have a name that matches the corresponding custom tag in the
    xml option parsing file.

    Code here will run before the reactor starts, and can safely block.
    """

    def __init__(self, action):
        m = getattr(self, action, None)
        if not m:
            raise AquilonError("Internal Error: Unknown action '%s' attempted"
                    % action)
        self.run = m

    def create_bundle(self, commandOptions):
        from subprocess import Popen, PIPE
        from re import search
        from tempfile import mkstemp
        from base64 import b64encode

        p = Popen(("git", "status"), stdout=PIPE, stderr=2)
        (out, err) = p.communicate()
        if p.returncode:
            sys.stdout.write(out)
            print >>sys.stderr, "Error running git status, returncode %d" \
                    % p.returncode
            sys.exit(1)
        if not search("nothing to commit", out):
            print >>sys.stderr, "Not ready to commit: %s" % out
            sys.exit(1)

        (handle, filename) = mkstemp()
        try:
            rc = Popen(("git", "bundle", "create", filename, "HEAD"),
                        stdout=1, stderr=2).wait()
            if rc:
                print >>sys.stderr, \
                        "Error running git bundle create, returncode %d" % rc
                sys.exit(1)
    
            commandOptions["bundle"] = b64encode(file(filename).read())
        finally:
            os.unlink(filename)


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
        (command, transport, commandOptions, globalOptions) = \
                parser.getOptions()
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

    # Add the formatting option into the string.  This is only tricky if
    # a query operator has been specified, otherwise it would just be
    # tacking on (for example) .html to the uri.
    if globalOptions.has_key('format'):
        query_index = uri.find('?')
        extension = '.' + globalOptions["format"]
        if query_index > -1:
            uri = uri[:query_index] + extension + uri[query_index:]
        else:
            uri = uri + '.' + globalOptions["format"]

    if globalOptions.get('usesock'):
        from aquilon.client.socketwrappers import getPage
    elif globalOptions.get('noknc'):
        from aquilon.client.ncwrappers import getPage
    else:
        from aquilon.client.kncwrappers import getPage

    if transport.custom:
        action = CustomAction(transport.custom)
        action.run(commandOptions)

    # Not sure why some of the options are unicode...
    cleanOptions = {}
    for k, v in commandOptions.iteritems():
        cleanOptions[str(k)] = str(v)

    if transport.method == 'get':
        # All command line options are (hopefully) in the URI already.
        # Might also get away without something like this:
        # uri = uri + '?' + urllib.urlencode(config['parameters'])
        d = RESTResource(uri).get()
    elif transport.method == 'put':
        # FIXME: This will need to be more complicated.
        # In some cases, we may even need to call code here.
        putData = urllib.urlencode(cleanOptions)
        mimeType = 'application/x-www-form-urlencoded'
        d = RESTResource(uri).put(putData, mimeType)
    elif transport.method == 'delete':
        # Again, all command line options should be in the URI already.
        d = RESTResource(uri).delete()
    elif transport.method == 'post':
        d = RESTResource(uri).post(**cleanOptions)
    else:
        print >>sys.stderr, "Unhandled transport method ", transport.method
        sys.exit(1)

    d = d.addCallback(gotPage, uri, transport.expect, globalOptions)
    d = d.addErrback(handleFailure)
    d = d.addCallback(lambda _: reactor.stop())

    #import pdb
    #pdb.set_trace()
    reactor.run()

