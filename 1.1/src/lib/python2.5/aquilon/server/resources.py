#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''The main class here is ResponsePage, which contains all the methods
for implementing the various aq commands.

To implement a command, define a transport for it in input.xml and
then add a command_<name>[_trigger] method to the ResponsePage class.
Any variables in the URL itself will be available as 
request.path_variable["varname"] where "varname" is the name of the
option.

The pages are built up at server start time based on the definitions in
the server's input.xml.  The RestServer class (which itself inherits
from ResponsePage for serving requests) contains this magic.  This
class builds out all the ResponsePage children as part of its __init__.

For any given ResponsePage, all methods (including all the command_
methods) are available, but only the expected methods for that relative
URL will be assigned to render_GET, render_POST, etc.  The rest will be
dormant.

Coming soon: the ResponsePage should provide some massaging for
incoming data, or at least handle requests for different output
formats consistently.  It can/should also provide some helpers for
those output formats.
'''

import re
import sys
import os
import xml.etree.ElementTree as ET

from twisted.application import internet
from twisted.web import server, resource, http, error
from twisted.internet import defer, utils
from twisted.python import log

from aquilon.server.exceptions_ import AuthorizationException

class ResponsePage(resource.Resource):
    def __init__(self, dbbroker, azbroker, path, path_variable=None):
        self.path = path
        self.dbbroker = dbbroker
        self.azbroker = azbroker
        self.path_variable = path_variable
        self.dynamic_child = None
        resource.Resource.__init__(self)

    def getChild(self, path, request):
        """Typically in twisted.web, a dynamic child would be created...
        dynamically.  However, to make the command_* mappings possible,
        they were all created at start time.

        This is an issue because the path cannot be handed to the
        constructor for it to deal with variable path names.  Instead,
        the request object is abused - the variable path names are
        crammed into it before handing back the child that is being
        requested.

        """

        if not self.dynamic_child:
            return resource.Resource.getChild(self, path, request)
        if not getattr(request, "path_variables", None):
            request.path_variables = {}
        request.path_variables[self.dynamic_child.path_variable] = path
        return self.dynamic_child

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

    def command_show_host_all(self, request):
        """aqcommand: aq show host --all"""
        #print 'render_GET called'
        try:
            self.azbroker.check(None, request.channel.getPrinciple(), "show",
                                "/host")
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        #d = self.dbbroker.showHostAll(session=True)
        #d = d.addErrback( self.wrapError, request )
        #d = d.addCallback( self.wrapHostInTable )
        #d = d.addCallback( self.wrapTableInBody )
        #d = d.addCallback( self.finishRender, request )
        #d = d.addErrback(log.err)
        #return server.NOT_DONE_YET
        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq show_host --all has not been implemented yet"
    
    def command_show_host_hostname(self, request):
        """aqcommand: aq show host --hostname=<host>"""
        #print 'render_GET called'
        #name = request.args['name'][0]
        #name = self.path
        name = request.path_variables["hostname"]

        try:
            self.azbroker.check(None, request.channel.getPrinciple(), "show",
                                "/host/%s" % name)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        #d = self.dbbroker.showHost(name, session=True)
        #d = d.addErrback( self.wrapError, request )
        #d = d.addCallback( self.wrapHostInTable )
        #d = d.addCallback( self.wrapTableInBody )
        #d = d.addCallback( self.finishRender, request )
        #d = d.addErrback(log.err)
        #return server.NOT_DONE_YET
        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq show_host --hostname has not been implemented yet"

    def command_add_host(self, request):
        """aqcommand: aq add host --hostname=<host>"""
        #name = request.args['name'][0]
        #request.content.seek(0)
        #name = self.path
        name = request.path_variables["hostname"]

        try:
            self.azbroker.check(None, request.channel.getPrinciple(), "add",
                                "/host/%s" % name)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        #d = self.dbbroker.addHost(name, session=True)
        ## FIXME: Trap specific exceptions (host exists, etc.)
        #d = d.addErrback( self.wrapError, request )
        #d = d.addCallback( self.wrapHostInTable )
        #d = d.addCallback( self.wrapTableInBody )
        #d = d.addCallback( self.finishRender, request )
        #d = d.addErrback(log.err)
        #return server.NOT_DONE_YET
        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add_host has not been implemented yet"

    def command_del_host(self, request):
        """aqcommand: aq del host --hostname=<host>"""
        #name = self.path
        name = request.path_variables["hostname"]

        try:
            self.azbroker.check(None, request.channel.getPrinciple(), "del",
                                "/host/%s" % name)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        #d = self.dbbroker.delHost(name, session=True)
        ## FIXME: Trap specific exceptions (host exists, etc.)
        #d = d.addErrback( self.wrapError, request )
        #d = d.addCallback( self.finishOK, request )
        #d = d.addErrback(log.err)
        #return server.NOT_DONE_YET
        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq del_host has not been implemented yet"

    def command_pxeswitch(self, request):
        """aqcommand: aq pxeswitch --hostname=<host>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq pxeswitch has not been implemented yet"

    def command_assoc(self, request):
        """aqcommand: aq assoc --hostname=<host>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq assoc has not been implemented yet"

    def command_reconfigure(self, request):
        """aqcommand: aq reconfigure --hostname=<host>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq reconfigure has not been implemented yet"

    def command_cat_hostname(self, request):
        """aqcommand: aq cat --hostname=<host>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq cat --hostname has not been implemented yet"

    def command_cat_template(self, request):
        """aqcommand: aq cat --template=<template> --domain=<domain>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq cat --template has not been implemented yet"

    def command_add_domain(self, request):
        """aqcommand: aq add domain --domain=<domain>"""
        #name = self.path
        domain = request.path_variables["domain"]

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add_domain has not been implemented yet"

    def command_del_domain(self, request):
        """aqcommand: aq del domain --domain=<domain>"""
        #name = self.path
        domain = request.path_variables["domain"]

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq del_domain has not been implemented yet"

    def command_add_template(self, request):
        """aqcommand: aq add template --name=<name> --domain=<domain>"""
        #name = self.path
        domain = request.path_variables["domain"]
        template = request.path_variables["name"]

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add_template has not been implemented yet"

    def command_get(self, request):
        """aqcommand: aq get --domain=<domain>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq get has not been implemented yet"

    def command_put(self, request):
        """aqcommand: aq put --domain=<domain>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq put has not been implemented yet"

    def command_deploy(self, request):
        """aqcommand: aq deploy --domain=<domain> --to=<domain>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq deploy has not been implemented yet"

    def command_manage(self, request):
        """aqcommand: aq manage --hostname=<name> --domain=<domain>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq manage has not been implemented yet"

    def command_sync(self, request):
        """aqcommand: aq sync --domain=<domain>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq sync has not been implemented yet"

    def command_show_location(self, request):
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
    
    def command_show_location_type(self, request):
        """aqcommand: aq show location --type"""
        #type = self.path
        type = request.path_variables["type"]
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
    
    def command_show_location_name(self, request):
        """aqcommand: aq show location --name=<location>"""
        #print 'render_GET called'
        #name = request.args['name'][0]
        #name = self.path
        type = request.path_variables["type"]
        name = request.path_variables["name"]

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

    def command_add_location(self, request):
        """aqcommand: aq add location --locationname=<location>"""
        #name = request.args['name'][0]
        #request.content.seek(0)
        #name = self.path
        type = request.path_variables["type"]
        name = request.path_variables["name"]

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

    def command_del_location(self, request):
        """aqcommand: aq del location --locationname=<location>"""
        #name = self.path
        type = request.path_variables["type"]
        name = request.path_variables["name"]

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

    def command_run_dummy_command(self, request):
        def _cb_command_output((out, err, code)):
            log.msg("echo finished with return code %d" % code)
            # FIXME: do stuff with err and code
            return out

        def _cb_command_error((out, err, signalNum)):
            # FIXME: do stuff with err and signalNum
            return out

        d = utils.getProcessOutputAndValue("/bin/echo",
                [ "/bin/env && echo hello && sleep 1 && echo hi; echo bye" ] )
        d = d.addErrback( self.wrapError, request )
        d = d.addCallbacks(_cb_command_output, _cb_command_error)
        d = d.addCallback( self.finishRender, request )
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET

    def command_status(self, request):
        """aqcommand: aq status"""

        try:
            self.azbroker.check(None, request.channel.getPrinciple(), "show",
                                "/")
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        return "<html><head><title>Status</title></head><body>OK</body></html>"

    # FIXME: Probably going to change...
    def command_add_hardware(self, request):
        """aqcommand: aq add hardware --location=<location>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add hardware has not been implemented yet"

    # FIXME: Probably going to change...
    def command_add_model(self, request):
        """aqcommand: aq add model --os=<os> --model=<model> --domain=<domain>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add model has not been implemented yet"

    # FIXME: Probably going to change...
    def command_add_service(self, request):
        """aqcommand: aq add service --service=<service> --domain=<domain>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add service has not been implemented yet"

    # FIXME: Probably going to change...
    def command_add_service_instance(self, request):
        """aqcommand: aq add service --service=<service> --domain=<domain> --instance=<instance>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add service --instance has not been implemented yet"

    # FIXME: Probably going to change...
    def command_bind_service(self, request):
        """aqcommand: aq bind service --service=<service> --hostname=<hostname>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq bind service has not been implemented yet"


class RestServer(ResponsePage):
    """The root resource is used to define the site as a whole."""
    def __init__(self, dbbroker, azbroker):
        ResponsePage.__init__(self, dbbroker, azbroker, '')

        # Regular Expression for matching variables in a path definition.
        varmatch = re.compile(r'^%\((.*)\)s$')

        BINDIR = os.path.dirname( os.path.realpath(sys.argv[0]) )
        tree = ET.parse( os.path.join( BINDIR, '..', 'etc', 'input.xml' ) )

        for command in tree.getiterator("command"):
            for transport in command.getiterator("transport"):
                if not command.attrib.has_key("name") \
                        or not transport.attrib.has_key("method") \
                        or not transport.attrib.has_key("path"):
                    continue
                name = command.attrib["name"]
                method = transport.attrib["method"]
                path = transport.attrib["path"]
                trigger = transport.attrib.get("trigger")
                container = self
                relative = ""
                # Traverse down the resource tree, container will
                # end up pointing to the correct spot.
                # Create branches and leaves as necessary, continueing to
                # traverse downward.
                for component in path.split("/"):
                    relative = relative + "/" + component
                    #log.msg("Working with component '" + component + "' of '" + relative + "'.")
                    m = varmatch.match(component)
                    # Is this piece of the path dynamic?
                    if not m:
                        #log.msg("Component '" + component + "' is static.")
                        child = container.getStaticEntity(component)
                        if child is None:
                            #log.msg("Creating new static component '" + component + "'.")
                            child = ResponsePage(self.dbbroker, self.azbroker,
                                                    relative)
                            container.putChild(component, child)
                        container = child
                    else:
                        #log.msg("Component '" + component + "' is dynamic.")
                        path_variable = m.group(1)
                        if container.dynamic_child is not None:
                            #log.msg("Dynamic component '" + component + "' already exists.")
                            current_variable = container.dynamic_child.\
                                    path_variable
                            if current_variable != path_variable:
                                log.err("Could not use variable '"
                                        + path_variable + "', already have "
                                        + "dynamic variable '" 
                                        + current_variable + "'.")
                                # XXX: Raise an error if they don't match
                                container = container.dynamic_child
                            else:
                                #log.msg("Dynamic component '" + component + "' had correct variable.")
                                container = container.dynamic_child
                        else:
                            #log.msg("Creating new dynamic component '" + component + "'.")
                            child = ResponsePage(self.dbbroker, self.azbroker,
                                                    relative,
                                                    path_variable=path_variable)
                            container.dynamic_child = child
                            container = child

                fullcommand = name
                if trigger:
                    fullcommand = fullcommand + "_" + trigger
                # If the command has not been implemented yet, the server
                # will bail out on startup with something like:
                # AttributeError: ResponsePage instance has no attribute
                #  'command_xxx'
                # Go create it, or fix the command/transport definition.
                mycommand = getattr(container, "command_" + fullcommand)
                rendermethod = "render_" + method.upper()
                if getattr(container, rendermethod, None):
                    # FIXME: Raise an Error, something has already been added
                    log.err("Already have a %s here at %s..." %
                            (rendermethod, container.path))
                #log.msg("Setting 'command_" + fullcommand + "' as '" + rendermethod + "' for container '" + container.path + "'.")
                setattr(container, rendermethod, mycommand)

        def _logChildren(level, container):
            for (key, child) in container.listStaticEntities():
                log.msg("Resource at level %d for %s [key:%s]"
                        % (level, child.path, key))
                _printChildren(level+1, child)
            if container.dynamic_child:
                log.msg("Resource at level %d for %s [dynamic]"
                        % (level, container.dynamic_child.path))
                _printChildren(level+1, container.dynamic_child)

        #_logChildren(0, self)

