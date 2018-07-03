#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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

'''Client for accessing aqd.

It uses knc by default for an authenticated connection, but can also
connect directly.

'''

from __future__ import print_function

import sys
import os
import re
import subprocess
import socket
import csv
from threading import Thread

# -- begin path_setup --
BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
LIBDIR = os.path.join(BINDIR, "..", "lib")

if LIBDIR not in sys.path:
    sys.path.append(LIBDIR)
# -- end path_setup --

from aquilon.client import depends  # pylint: disable=W0611
from aquilon.config import lookup_file_path, get_username
from aquilon.exceptions_ import AquilonError
from aquilon.client.knchttp import KNCHTTPConnection
from aquilon.client.chunked import ChunkedHTTPConnection
from aquilon.client.optparser import OptParser, ParsingError
from aquilon.python_patches import load_uuid_quickly

from six.moves.urllib_parse import urlencode, quote  # pylint: disable=F0401
from six.moves.configparser import SafeConfigParser  # pylint: disable=F0401
import six.moves.http_client as httplib  # pylint: disable=F0401
from six import iteritems

# Stolen from aquilon.worker.formats.fomatters
csv.register_dialect('aquilon', delimiter=',', quoting=csv.QUOTE_MINIMAL,
                     doublequote=True, lineterminator='\n')


class RESTResource(object):
    def __init__(self, httpconnection, uri):
        self.httpconnection = httpconnection
        self.uri = uri

    def get(self):
        return self._sendRequest('GET')

    def post(self, **kwargs):
        postData = urlencode(kwargs)
        mimeType = 'application/x-www-form-urlencoded'
        return self._sendRequest('POST', postData, mimeType)

    def put(self, data, mimeType):
        return self._sendRequest('PUT', data, mimeType)

    def delete(self):
        return self._sendRequest('DELETE')

    def _sendRequest(self, method, data=None, mimeType=None):
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

    def __init__(self, action, options):
        m = getattr(self, action, None)
        if not m:
            raise AquilonError("Internal Error: Unknown action '%s' attempted"
                               % action)
        self.run = m

        # Propagate some options to subprocesses
        self.env = os.environ.copy()
        self.env["AQHOST"] = options.get("aqhost")
        self.env["AQSERVICE"] = options.get("aqservice")
        self.env["AQPORT"] = str(options.get("aqport"))

    def create_bundle(self, commandOptions):
        from subprocess import Popen, PIPE
        from tempfile import mkstemp
        from base64 import b64encode

        p = Popen(("git", "fetch"), stderr=2)
        p.wait()  # wait for return, but it's okay if this fails
        p = Popen(("git", "status", "--porcelain"), stdout=PIPE, stderr=2)
        (out, err) = p.communicate()
        if p.returncode:
            print("\nError running git status --porcelain, returncode %d" %
                  p.returncode, file=sys.stderr)
            sys.exit(1)
        if out:
            print("Not ready to publish, found:\n%s" % out, file=sys.stderr)
            sys.exit(1)

        # Locate the top of the sandbox for the purposes of executing the
        # unit tests in the t directory
        p = Popen(('git', 'rev-parse', '--show-toplevel'), stdout=PIPE)
        (sandbox_dir, err) = p.communicate()
        sandbox_dir = sandbox_dir.strip()
        if p.returncode != 0:
            print("Failed to find toplevel of sandbox, aborting", file=sys.stderr)
            sys.exit(1)
        # Prevent the branch being published unless the unit tests pass
        testdir = os.path.join(sandbox_dir, 't')
        if os.path.exists(os.path.join(testdir, 'Makefile')):
            p = Popen(['/usr/bin/make', '-C', testdir, 'test',
                       'AQCMD=%s' % os.path.realpath(sys.argv[0]),
                       'AQBUILDXML=%s' % lookup_file_path("build.xml")],
                      cwd=testdir, env=self.env)
            p.wait()
            if p.returncode != 0:
                print("\nUnit tests failed, publish prohibited.", end=' ',
                      file=sys.stderr)
                print('(Do you need to run a "make clean test"?)',
                      file=sys.stderr)
                sys.exit(1)

        if "sandbox" in commandOptions:
            branch = commandOptions["sandbox"]
        else:
            branch = commandOptions["branch"]
        revlist = "origin/%s..HEAD" % branch
        p = Popen(("git", "log", revlist), stdout=PIPE, stderr=2)
        (out, err) = p.communicate()

        if out:
            print("\nThe following changes will be included in this push:\n",
                  file=sys.stdout)
            print("------------------------", file=sys.stdout)
            print(str(out), file=sys.stdout)
            print("------------------------", file=sys.stdout)
        else:
            print("\nYou haven't made any changes on this branch\n",
                  file=sys.stdout)
            sys.exit(0)

        (handle, filename) = mkstemp()
        try:
            rc = Popen(("git", "bundle", "create", filename, revlist),
                       stdout=1, stderr=2).wait()
            if rc:
                print("Error running git bundle create, returncode %d" % rc,
                      file=sys.stderr)
                sys.exit(1)

            commandOptions["bundle"] = b64encode(open(filename).read())
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
        print("Cannot access user directory '%s'.  Is the share mounted and "
              "visible?" % user_base, file=sys.stderr)
        return 1
    sandbox_dir = os.path.join(user_base, sandbox_name)
    if os.path.exists(sandbox_dir):
        # This check is done broker-side as well.  This code should be
        # exercised rarely (and probably never).
        print("Sandbox directory '%s' already exists.  Use `git fetch` to "
              "update it or remove the directory and run `aq get`." %
              sandbox_dir, file=sys.stderr)
        return 1
    os.umask(0o022)
    cmd = ("git", "clone", "--branch", sandbox_name,
           template_king_url, sandbox_name)
    if noexec:
        print("cd '%s'" % user_base)
        print(" ".join("'%s'" % c for c in cmd))
        return 0
    try:
        p = subprocess.Popen(cmd, cwd=user_base, stdin=None,
                             stdout=1, stderr=2)
    except OSError as e:
        print("Could not execute %s: %s" % (cmd, e), file=sys.stderr)
        return 1
    exit_status = p.wait()
    if exit_status == 0:
        print("Created sandbox: %s" % sandbox_dir)
    return exit_status


class StatusThread(Thread):
    def __init__(self, aqhost, aqport, authuser, requestid=None, auditid=None,
                 debug=False, outstream=sys.stderr, **kwargs):
        self.host = aqhost
        self.port = aqport
        self.authuser = authuser
        self.requestid = requestid
        self.auditid = auditid
        self.finished = False
        self.debug = debug
        self.response_status = None
        self.outstream = outstream
        self.waiting_for_request = True
        Thread.__init__(self)

        # Don't block the process exiting if this thread is still around
        self.daemon = True

    def run(self):
        try:
            self.show_request()
        except:
            # Weird stuff can happen in threads.  Just ignore it.
            pass

    def show_request(self):
        # print("Attempting status connection...", file=sys.stderr)
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
            sconn.set_debuglevel(10)
        if self.auditid:
            uri = "/status/auditid/%s%s" % (self.auditid, parameters)
        else:
            uri = "/status/requestid/%s%s" % (self.requestid, parameters)
        RESTResource(sconn, uri).get()
        # handle failed requests
        res = sconn.getresponse()
        self.response_status = res.status

        if res.status != httplib.OK:
            if self.debug:
                print("%s: %s" % (httplib.responses[res.status], res.read()),
                      file=sys.stderr)
            sconn.close()
            return

        while res.fp:
            pageData = res.read_chunk()
            if pageData:
                self.outstream.write(pageData)
        sconn.close()
        return


def quoteOptions(options):
    return "&".join(quote(k) + "=" + quote(v) for k, v in iteritems(options))


def get_default_opts(auth_option, conf_file=None):

    config = SafeConfigParser()

    if not conf_file:
        # By default, always use the system-wide config file if present
        if globalOptions.get('develmode'):
            check_conf_in_sources = False
        else:
            check_conf_in_sources = True
        conf_file = lookup_file_path("aq.conf", check_conf_in_sources=check_conf_in_sources)

    if conf_file:
        config.read(conf_file)
        config_options = {}
        if not auth_option and config.has_section("readonly"):
            config_options = dict(config.items("readonly"))
        if not config_options and config.has_section("defaults"):
            config_options = dict(config.items("defaults"))
        return config_options


if __name__ == "__main__":
    # Set up the search path for man pages. "man" does not like ".." in the
    # path, so we have to normalize it
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    MANDIR = os.path.realpath(os.path.join(BINDIR, "..", "doc", "man"))
    if os.path.exists(MANDIR):
        if "MANPATH" in os.environ:
            os.environ["MANPATH"] = MANDIR + ":" + os.environ["MANPATH"]
        else:
            os.environ["MANPATH"] = MANDIR

    parser = OptParser(lookup_file_path('input.xml'))
    try:
        (command, transport, commandOptions, globalOptions) = \
            parser.parse(sys.argv[1:])
    except ParsingError as e:
        print('%s: %s' % (sys.argv[0], e.error), file=sys.stderr)
        print('%s: Try --help for usage details.' % (sys.argv[0]),
              file=sys.stderr)
        sys.exit(1)

    # if a client config file is specified on command line
    # that should overide  env or default options.
    if globalOptions.get('aqconf'):
        globalOptions.update(get_default_opts(globalOptions.get('auth'),
                                              globalOptions.get('aqconf')))
    else:
        defaultOpts = get_default_opts(globalOptions.get('auth'))

    # Default for /ms/dist
    if re.match(r"/ms(/.(global|local)/[^/]+)?/dist/", BINDIR):
        default_aqhost = defaultOpts.get('aqhost') or 'nyaqd1'
        default_aqservice = 'cdb'
    # Default for /ms/dev
    elif re.match(r"/ms(/.(global|local)/[^/]+)?/dev/", BINDIR):
        default_aqhost = defaultOpts.get('aqhost') or 'nyaqd1'
        default_aqservice = 'cdb'
    else:
        default_aqhost = socket.gethostname()
        default_aqservice = get_username()

    host = globalOptions.get('aqhost') or os.environ.get('AQHOST', None) or \
        default_aqhost

    port = globalOptions.get('aqport') or os.environ.get('AQPORT', None) or \
        defaultOpts.get('aqport')

    if globalOptions.get('auth'):
        port = port or 6900
    else:
        port = port or 6901

    if globalOptions.get('aqservice'):
        aqservice = globalOptions.get('aqservice')
    elif os.environ.get('AQSERVICE', None):
        aqservice = os.environ['AQSERVICE']
    elif globalOptions.get('aquser'):
        print("WARNING: --aquser is deprecated, please use --aqservice",
              file=sys.stderr)
        aqservice = globalOptions.get('aquser')
    elif os.environ.get('AQUSER', None):
        print("WARNING: AQUSER environment variable is deprecated, please use "
              "AQSERVICE", file=sys.stderr)
        aqservice = os.environ['AQUSER']
    else:
        aqservice = defaultOpts.get('aqservice') or default_aqservice or get_username()

    # Save these in case there are errors...
    globalOptions["aqhost"] = host
    globalOptions["aqport"] = port
    globalOptions["aqservice"] = aqservice

    if transport is None:
        print("Unimplemented command ", command, file=sys.stderr)
        exit(1)

    # Convert unicode options to strings
    newOptions = {}
    for k, v in iteritems(commandOptions):
        newOptions[str(k)] = str(v)
    commandOptions = newOptions
    # Should maybe have an input.xml flag on which global options
    # to include... for now it's just debug.
    if globalOptions.get("debug", None):
        commandOptions["debug"] = str(globalOptions["debug"])
    if command != "show_request" and globalOptions.get("verbose"):
        uuid = load_uuid_quickly()
        commandOptions["requestid"] = str(uuid.uuid4())

    # Quote options so that they can be safely included in the URI
    cleanOptions = {}
    for k, v in iteritems(commandOptions):
        # urllib.quote() does not escape '/' by default. We have to turn off
        # this behavior because otherwise a parameter containing '/' would
        # confuse the URL parsing logic on the server side.
        cleanOptions[k] = quote(v, safe='')

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
    if 'format' in globalOptions and not transport.expect:
        extension = '.' + quote(globalOptions["format"])

        query_index = uri.find('?')
        if query_index > -1:
            uri = uri[:query_index] + extension + uri[query_index:]
        else:
            uri = uri + extension

    authuser = globalOptions.get('auth') and aqservice or None
    # create HTTP connection object adhering to the command line request
    if authuser:
        conn = KNCHTTPConnection(host, port, authuser)
    else:
        conn = ChunkedHTTPConnection(host, port)

    if globalOptions.get('debug'):
        conn.set_debuglevel(10)

    # run custom command if there's one
    if transport.custom:
        action = CustomAction(transport.custom, globalOptions)
        action.run(commandOptions)

    status_thread = None
    # Kick off a thread to (potentially) get status...
    # Spare a second connection to the server for read-only commands that use
    # the "GET" method
    if command == "show_request" or (transport.method != "get" and
                                     globalOptions.get("verbose")):
        status_thread = StatusThread(host, port, authuser, **commandOptions)

    if command == "show_request":
        status_thread.outstream = sys.stdout
        status_thread.start()
        status_thread.join()
        if not status_thread.response_status or \
           status_thread.response_status == httplib.OK:
            sys.exit(0)
        else:
            sys.exit(status_thread.response_status // 100)

    if status_thread:
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
            putData = urlencode(commandOptions)
            mimeType = 'application/x-www-form-urlencoded'
            RESTResource(conn, uri).put(putData, mimeType)

        elif transport.method == 'post':
            RESTResource(conn, uri).post(**commandOptions)

        else:
            print("Unhandled transport method ", transport.method,
                  file=sys.stderr)
            sys.exit(1)

        res = conn.getresponse()

    except (httplib.HTTPException, socket.error) as e:
        # noauth connections
        if not hasattr(conn, "getError"):
            print("Error: %s" % e, file=sys.stderr)
            sys.exit(1)
        # KNC connections
        msg = conn.getError()
        host_failed = "Failed to connect to %s" % host
        port_failed = "%s port %s" % (host_failed, port)
        if msg.find(b'Connection refused') >= 0:
            print("%s: Connection refused." % port_failed, file=sys.stderr)
        elif msg.find(b'Connection timed out') >= 0:
            print("%s: Connection timed out." % port_failed, file=sys.stderr)
        elif msg.find(b'Unknown host') >= 0:
            print("%s: Unknown host." % host_failed, file=sys.stderr)
        else:
            print("Error: %s: %s" % (repr(e), msg), file=sys.stderr)
        sys.exit(1)

    pageData = res.read()

    # Wait for additional status messages to arrive, but not for long
    if status_thread:
        status_thread.join(5)

    if res.status != httplib.OK:
        print("%s: %s" % (httplib.responses.get(res.status, res.status),
                          pageData), file=sys.stderr)
        if res.status == httplib.MULTI_STATUS and \
           globalOptions.get('partialok'):
            sys.exit(0)
        sys.exit(res.status // 100)

    exit_status = 0

    if transport.expect == 'command':
        if not globalOptions.get('exec'):
            print(pageData)
        else:
            try:
                proc = subprocess.Popen(pageData, shell=True, stdin=sys.stdin,
                                        stdout=sys.stdout, stderr=sys.stderr)
            except OSError as e:
                print(e, file=sys.stderr)
                sys.exit(1)

            exit_status = proc.wait()
    elif transport.expect == 'sandbox':
        noexec = not globalOptions.get('exec')
        exit_status = create_sandbox(pageData, noexec=noexec)
    else:
        if res.getheader('content-type').startswith('text/'):
            # TODO: honour the charset in the header, if any - not that the
            # broker would use anything else
            pageData = pageData.decode("utf-8")
            sys.stdout.write(pageData)
            # The CSV formatter adds a terminating newline, raw formatters not
            # necessarily
            if pageData and not pageData.endswith("\n"):
                sys.stdout.write("\n")
        else:
            # Non-text result - avoid buffering and charset conversion
            os.write(sys.stdout.fileno(), pageData)

    sys.exit(exit_status)
