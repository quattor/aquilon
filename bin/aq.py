#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.

'''Client for accessing aqd.

It uses knc by default for an authenticated connection, but can also
connect directly.

'''


import sys
import os
import urllib
import re
import subprocess
import socket
import httplib
import uuid
import csv
from time import sleep
from threading import Thread

BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(os.path.join(BINDIR, "..", "lib", "python2.6"))

from aquilon.client.knchttp import KNCHTTPConnection
from aquilon.client.chunked import ChunkedHTTPConnection
from aquilon.client.optparser import OptParser, ParsingError

# Stolen from aquilon.server.formats.fomatters
csv.register_dialect('aquilon', delimiter=',', quoting=csv.QUOTE_MINIMAL,
                     doublequote=True, lineterminator='\n')

class RESTResource(object):
    def __init__(self, httpconnection, uri):
        self.httpconnection = httpconnection
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

    def _sendRequest(self, method, data = None, mimeType = None):
        headers = {}
        if mimeType:
            headers['Content-Type'] = mimeType
        self.httpconnection.request(method, self.uri, data, headers)

    def getresponse(self):
        return self.httpconnection.getresponse()


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

        p = Popen(("git", "fetch"), stderr=2)
        p.wait()  ## wait for return, but it's okay if this fails
        p = Popen(("git", "status", "--porcelain"), stdout=PIPE, stderr=2)
        (out, err) = p.communicate()
        if p.returncode:
            print >>sys.stderr, \
                    "\nError running git status --porcelain, returncode %d" \
                    % p.returncode
            sys.exit(1)
        if out:
            print >>sys.stderr, "Not ready to publish, found:\n%s" % out
            sys.exit(1)

        revlist = "origin/%s..HEAD" % commandOptions["branch"]
        p = Popen(("git", "log", revlist), stdout=PIPE, stderr=2)
        (out,err) = p.communicate()

        if out:
            print >>sys.stdout, "\nThe following changes will be included in this push:\n"
            print >>sys.stdout, "------------------------"
            print >>sys.stdout, str(out)
            print >>sys.stdout, "------------------------"
        else:
            print >>sys.stdout, "\nYou haven't made any changes on this branch\n"
            sys.exit(0)
            
        (handle, filename) = mkstemp()
        try:
            rc = Popen(("git", "bundle", "create", filename, revlist),
                        stdout=1, stderr=2).wait()
            if rc:
                print >>sys.stderr, \
                        "Error running git bundle create, returncode %d" % rc
                sys.exit(1)
    
            commandOptions["bundle"] = b64encode(file(filename).read())
        finally:
            os.unlink(filename)


def create_sandbox(pageData, noexec=False):
    output = pageData.splitlines()
    if not output or not output[0].strip():
        # The 'add' command may have no output if --noget was used,
        # but the 'get' command should always have something...
        return 0
    reader = csv.reader(output, dialect='aquilon')
    for row in reader:
        (template_king_url, sandbox_name, user_base) = row[0:3]
        break
    if not os.path.exists(user_base):
        print >>sys.stderr, "Cannot access user directory '%s'.  " \
                "Is the share mounted and visible?" % user_base
        return 1
    sandbox_dir = os.path.join(user_base, sandbox_name)
    if os.path.exists(sandbox_dir):
        # This check is done broker-side as well.  This code should be
        # exercised rarely (and probably never).
        print >>sys.stderr, "Sandbox directory '%s' already exists.  " \
                "Use `git fetch` to update it or remove the directory " \
                "and run `aq get`." % sandbox_dir
        return 1
    cmd = ("git", "clone", "--branch", sandbox_name,
           template_king_url, sandbox_name)
    if noexec:
        print "cd '%s'" % user_base
        print " ".join(["'%s'" % c for c in cmd])
        return 0
    try:
        p = subprocess.Popen(cmd, cwd=user_base, stdin=None, stdout=1, stderr=2)
    except OSError, e:
        print >>sys.stderr, "Could not execute %s: %s" % (cmd, e)
        return 1
    exit_status = p.wait()
    if exit_status == 0:
        print "Created sandbox: %s" % sandbox_dir
    return exit_status


class StatusThread(Thread):
    def __init__(self, host, port, authuser, requestid=None, auditid=None,
                 debug=False, outstream=sys.stderr, **kwargs):
        self.host = host
        self.port = port
        self.authuser = authuser
        self.requestid = requestid
        self.auditid = auditid
        self.finished = False
        self.debug = debug
        self.response_status = None
        self.retry = 5
        self.outstream = outstream
        self.waiting_for_request = True
        Thread.__init__(self)

    def run(self):
        try:
            self.show_request()
        except:
            # Weird stuff can happen in threads.  Just ignore it.
            pass

    def show_request(self):
        # Delay before attempting to retrieve status messages.
        # We want to give the main thread a chance to compose and send the
        # original request before we send the status request.
        while self.waiting_for_request:
            sleep(.1)
        #print >>sys.stderr, "Attempting status connection..."
        # Ideally we would always make a noauth connection here, but we
        # only know the port that's been specified for this command -
        # so it's either the auth port or it's not.
        if self.authuser:
            sconn = KNCHTTPConnection(self.host, self.port, self.authuser)
        else:
            sconn = ChunkedHTTPConnection(self.host, self.port)
        parameters = ""
        if self.debug:
            parameters = "?debug=True"
        if self.auditid:
            uri = "/status/auditid/%s%s" % (self.auditid, parameters)
        else:
            uri = "/status/requestid/%s%s" % (self.requestid, parameters)
        RESTResource(sconn, uri).get()
        # handle failed requests
        res = sconn.getresponse()
        self.response_status = res.status
        if res.status == httplib.NOT_FOUND and not self.finished and \
           self.retry > 0:
            sconn.close()
            self.retry -= 1
            # Maybe the command has not gotten to the server yet... retry.
            sleep(.1)
            return self.show_request()

        if res.status != httplib.OK:
            if self.debug:
                print >>sys.stderr, "%s: %s" % (httplib.responses[res.status],
                                                res.read())
            if self.retry <= 0:
                print >>sys.stderr, \
                        "Client status messages disabled, retries exceeded."
            sconn.close()
            return

        while res.fp:
            pageData = res.read_chunk()
            if pageData:
                print >>self.outstream, pageData
        sconn.close()
        return


def quoteOptions(options):
    return "&".join([ urllib.quote(k) + "=" + urllib.quote(v) for k, v in options.iteritems() ])


if __name__ == "__main__":
    parser = OptParser( os.path.join( BINDIR, '..', 'etc', 'input.xml' ) )
    try:
        (command, transport, commandOptions, globalOptions) = \
                parser.parse(sys.argv[1:])
    except ParsingError, e:
        print >>sys.stderr, '%s: Option parsing error: %s' % (sys.argv[0],
                                                              e.error)
        print >>sys.stderr, '%s: Try --help for usage details.' % (sys.argv[0])
        sys.exit(1)

    # Setting this as a global default.  It might make sense to set
    # the default to the current running user when running out of a
    # shadow, though.
    default_aquser = "cdb"

    # Default for /ms/dist
    if re.match(r"/ms(/.(global|local)/[^/]+)?/dist/", BINDIR):
        default_aqhost = "nyaqd1"
    # Default for /ms/dev
    elif re.match(r"/ms(/.(global|local)/[^/]+)?/dev/", BINDIR):
        default_aqhost = "nyaqd1"
    else:
        default_aqhost = socket.gethostname()

    if globalOptions.get('auth') == False:
        default_aqport = 6901
    else:
        default_aqport = 6900

    host = globalOptions.get('aqhost') or os.environ.get('AQHOST', None) or \
            default_aqhost
    port = globalOptions.get('aqport') or os.environ.get('AQPORT', None) or \
            default_aqport
    aquser = globalOptions.get('aquser') or os.environ.get('AQUSER', None) or \
            default_aquser
    if 'AQSLOWSTATUS' in os.environ and not globalOptions.get('slowstatus'):
        serial = str(os.environ['AQSLOWSTATUS']).strip().lower()
        false_values = ['false', 'f', 'no', 'n', '0', '']
        globalOptions['slowstatus'] = not serial in false_values

    # Save these in case there are errors...
    globalOptions["aqhost"] = host
    globalOptions["aqport"] = port

    if transport is None:
        print >>sys.stderr, "Unimplemented command ", command
        exit(1)

    # Convert unicode options to strings
    newOptions = {}
    for k, v in commandOptions.iteritems():
        newOptions[str(k)] = str(v)
    commandOptions = newOptions
    # Should maybe have an input.xml flag on which global options
    # to include... for now it's just debug.
    if globalOptions.get("debug", None):
        commandOptions["debug"] = str(globalOptions["debug"])
    if command != "show_request" and not globalOptions.get("quiet"):
        commandOptions["requestid"] = str(uuid.uuid1())

    # Quote options so that they can be safely included in the URI
    cleanOptions = {}
    for k, v in commandOptions.iteritems():
        cleanOptions[k] = urllib.quote(v)

    # Decent amount of magic here...
    # Even though the server connection might be tunneled through
    # knc, the easiest way to consistently address the server is with
    # a URI.  That's the first half.
    # The relative URI defined by transport.path comes from the xml
    # file used for options definitions.  This is a standard python
    # string formatting, with references to the options that might
    # be given on the command line.
    uri = str('/' + transport.path % cleanOptions)

    # Add the formatting option into the string.  This is only tricky if
    # a query operator has been specified, otherwise it would just be
    # tacking on (for example) .html to the uri.
    # Do not apply any formatting for commands (transport.expect == 'command').
    if globalOptions.has_key('format') and not transport.expect:
        extension = '.' + urllib.quote(globalOptions["format"])

        query_index = uri.find('?')
        if query_index > -1:
            uri = uri[:query_index] + extension + uri[query_index:]
        else:
            uri = uri + extension

    authuser = globalOptions.get('auth') and aquser or None
    # create HTTP connection object adhering to the command line request
    if authuser:
        conn = KNCHTTPConnection(host, port, authuser)
    else:
        conn = ChunkedHTTPConnection(host, port)

    if globalOptions.get('debug'):
        conn.set_debuglevel(10)

    # run custom command if there's one
    if transport.custom:
        action = CustomAction(transport.custom)
        action.run(commandOptions)

    status_thread = None
    # Kick off a thread to (potentially) get status...
    # Spare a second connection to the server for read-only commands that use
    # the "GET" method
    if command == "show_request" or (transport.method != "get" and \
                                     not globalOptions.get("quiet")):
        status_thread = StatusThread(host, port, authuser, **commandOptions)

    if command == "show_request":
        status_thread.outstream = sys.stdout
        status_thread.waiting_for_request = False
        status_thread.start()
        status_thread.join()
        if not status_thread.response_status or \
           status_thread.response_status == httplib.OK:
            sys.exit(0)
        else:
            sys.exit(status_thread.response_status / 100)

    # Normally the status thread will start right away.  We should delay
    # starting it on request - generally because the broker is running
    # with sqlite and can't reliably handle connections in parallel.
    if status_thread and not globalOptions.get("slowstatus"):
        status_thread.start()

    try:
        if transport.method == 'get' or transport.method == 'delete':
            # Fun hackery here to get optional parameters into the path...
            # First, figure out what was already included in the path,
            # looking for %(var)s.
            c = re.compile(r'(?<!%)%\(([^)]*)\)s')
            exclude = c.findall(transport.path)

            # Now, pull each of these out of the options.  This is not
            # strictly necessary, but simplifies the uri.
            remainder = commandOptions.copy()
            for e in exclude:
                remainder.pop(e, None)

            if remainder:
                # Almost done.  Just need to account for whether the uri
                # already has a query string.
                if uri.find("?") >= 0:
                    uri = uri + '&' + quoteOptions(remainder)
                else:
                    uri = uri + '?' + quoteOptions(remainder)
            if transport.method == 'get':
                RESTResource(conn, uri).get()
            elif transport.method == 'delete':
                RESTResource(conn, uri).delete()

        elif transport.method == 'put':
            # FIXME: This will need to be more complicated.
            # In some cases, we may even need to call code here.
            putData = urllib.urlencode(commandOptions)
            mimeType = 'application/x-www-form-urlencoded'
            RESTResource(conn, uri).put(putData, mimeType)

        elif transport.method == 'post':
            RESTResource(conn, uri).post(**commandOptions)

        else:
            print >>sys.stderr, "Unhandled transport method ", transport.method
            sys.exit(1)

        # handle failed requests
        if status_thread:
            status_thread.waiting_for_request = False
        res = conn.getresponse()

    except (httplib.HTTPException, socket.error), e:
        # noauth connections
        if not hasattr(conn, "getError"):
            print >>sys.stderr, "Error: %s" % e
            sys.exit(1)
        # KNC connections
        msg = conn.getError()
        if msg.find('Connection refused') >= 0:
            print >>sys.stderr, "Failed to connect to %(aqhost)s port %(aqport)s: Connection refused." % globalOptions
        elif msg.find('Unknown host') >= 0:
            print >>sys.stderr, "Failed to connect to %(aqhost)s: Unknown host." % globalOptions
        else:
            print >>sys.stderr, "Error: %s: %s" % (repr(e), msg)
        sys.exit(1)

    if status_thread:
        if globalOptions.get("slowstatus"):
            status_thread.start()
        # Re-join the thread here before printing data.
        # Hard-coded timeout of 10 seconds to wait for info, otherwise it
        # is silently dropped.
        status_thread.join(10)

    pageData = res.read()

    if res.status != httplib.OK:
        print >>sys.stderr, "%s: %s" % (
            httplib.responses.get(res.status, res.status), pageData)
        sys.exit(res.status / 100)

    exit_status = 0

    if transport.expect == 'command':
        if not globalOptions.get('exec'):
            print pageData
        else:
            try:
                proc = subprocess.Popen(pageData, shell = True, stdin = sys.stdin,
                                        stdout = sys.stdout, stderr = sys.stderr)
            except OSError, e:
                print >>sys.stderr, e
                sys.exit(1)

            exit_status = proc.wait()
    elif transport.expect == 'sandbox':
        noexec = not globalOptions.get('exec')
        exit_status = create_sandbox(pageData, noexec=noexec)
    else:
        format = globalOptions.get("format", None)
        if format == "proto" or format == "csv":
            sys.stdout.write(pageData)
        elif pageData:
            print pageData

    sys.exit(exit_status)
