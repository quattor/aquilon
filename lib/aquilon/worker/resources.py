# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""The main class here is ResponsePage, which contains all the methods
for implementing the various aq commands.

To implement a command, define a transport for it in input.xml and
then add a command_<name>[_trigger] method to the ResponsePage class.
Any variables in the URL itself will be available as
request.args["varname"][0] where "varname" is the name of the
option.  (Any normal query/post variables will also be in this dict.)

The pages are built up at server start time based on the definitions in
the server's input.xml.  The RestServer class (which itself inherits
from ResponsePage for serving requests) contains this magic.  This
class builds out all the ResponsePage children as part of its __init__.

For any given ResponsePage, all methods (including all the command_
methods) are available, but only the expected methods for that relative
URL will be assigned to render_GET, render_POST, etc.  The rest will be
dormant.

As the request comes in (and passes through the various
getChildWithDefault() calls) it will be checked for extensions that
match the available format functions.  A request for location.html,
for example, will retrieve 'location' and format it with format_html().

ToDo:
    - Possibly massage the incoming data - simplify lists back to
        single variables, handle put content, etc.
    - Add some sort of interface that can be implemented for
        objects to give hints on how they should be rendered.
    - Add other output formats (csv, xml, etc.).

"""

import re
import sys
import os
import xml.etree.ElementTree as ET

from twisted.web import server, resource, http
from twisted.internet import defer, threads
from twisted.python import log

from aquilon.aqdb.types import StringEnum
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.formats.formatters import ResponseFormatter
from aquilon.worker.broker import BrokerCommand, ERROR_TO_CODE
from aquilon.worker import commands
from aquilon.worker.processes import cache_version
from aquilon.utils import (force_int, force_float, force_boolean, force_ipv4,
                           force_mac, force_ascii, force_list, force_json_dict)

# Regular Expression for matching variables in a path definition.
# Currently only supports stuffing a single variable in a path
# component.
varmatch = re.compile(r'^%\((.*)\)s$')


class ResponsePage(resource.Resource):

    def __init__(self, path, formatter, path_variable=None):
        self.path = path
        self.path_variable = path_variable
        self.dynamic_child = None
        resource.Resource.__init__(self)
        self.formatter = formatter
        self.handlers = {}

    def getChildWithDefault(self, path, request):
        """Overriding this method to parse formatting requests out
        of the incoming resource request."""

        # A good optimization here would be to have the resource store
        # a compiled regular expression to use instead of this loop.
        for style in self.formatter.formats:
            #log.msg("Checking style: %s" % style)
            extension = "." + style
            if path.endswith(extension):
                #log.msg("Retrieving formatted child for dynamic page: %s" % path)
                request.output_format = style
                # Chop off the extension when searching for children
                path = path[:-len(extension)]
                break
        return resource.Resource.getChildWithDefault(self, path, request)

    def getChild(self, path, request):
        """Typically in twisted.web, a dynamic child would be created...
        dynamically.  However, to make the command_* mappings possible,
        they were all created at start time.

        This is an issue because the path cannot be handed to the
        constructor for it to deal with variable path names.  Instead,
        the request object is abused - the variable path names are
        crammed into the data structure used for query and post
        arguments before handing back the child that is being
        requested.

        This method also checks to see if a format has been requested,
        and tucks that info away in the request object as well.  This
        is done for the static objects simply by replicating them at
        creation time - one for each style.
        """

        if not self.dynamic_child:
            return resource.Resource.getChild(self, path, request)

        #log.msg("Retrieving child for dynamic page: %s" % path)
        request.args[self.dynamic_child.path_variable] = [path]
        return self.dynamic_child

    def render(self, request):
        """This is based on the default implementation from
        resource.Resource that checks for the appropriate method to
        delegate to.

        It adds a default handler for arguments in a PUT request and
        delegation of argument parsing.
        The processing is pushed off onto a thread and wrapped with
        error handling.

        """
        if request.method == 'PUT':
            # For now, assume all put requests use a simple urllib encoding.
            request.content.seek(0)
            # Since these are both lists, there is a theoretical case where
            # one might want to merge the lists, instead of overwriting with
            # the new.  Not sure if that matters right now.
            request.args.update(http.parse_qs(request.content.read()))
        # FIXME: This breaks HEAD and OPTIONS handling...
        handler = self.handlers.get(request.method, None)
        if not handler:
            # FIXME: This may be broken, if it is supposed to get a useful
            # message based on available render_ methods.
            raise server.UnsupportedMethod(getattr(self, 'allowedMethods', ()))
        # Default render would just call the method here.
        # This is expanded to do argument checking, finish the request,
        # and do some error handling.
        d = self.check_arguments(request, handler.required_parameters,
                                 handler.optional_parameters,
                                 handler.parameter_checks)
        style = getattr(self, "output_format", None)
        if style is None:
            style = getattr(request, "output_format", None)
        if style is None:
            style = getattr(handler, "default_style", "raw")
        # The logger used to be set up after the session.  However,
        # this keeps a record of the request from forming immediately
        # if all the sqlalchmey session threads are in use.
        # This will be a problem if/when we want an auditid to come
        # from the database, but we can revisit at that point.
        d = d.addCallback(lambda arguments: handler.add_logger(style=style,
                                                               request=request,
                                                               **arguments))
        if handler.defer_to_thread:
            d = d.addCallback(lambda arguments: threads.deferToThread(
                handler.render, **arguments))
        else:
            d = d.addCallback(lambda arguments: handler.render(**arguments))
        d = d.addCallback(self.finishRender, request)
        d = d.addErrback(self.wrapNonInternalError, request)
        d = d.addErrback(self.wrapError, request)
        return server.NOT_DONE_YET

    def check_arguments(self, request, required=None, optional=None,
                        parameter_checks=None):
        """Check for the required and optional arguments.

        Returns a Deferred that will have a dictionary of the arguments
        found.  Any unsupplied optional arguments will have a value of
        None.  If there are any problems, the Deferred will errback with
        a failure.

        As a hack, debug is always allowed as an argument.  Should
        maybe have a flag on global options in input.xml for this.

        As a separate hack, requestid is always allowed as an
        argument.  This allows for status/update requests by the
        client before the command returns.

        """

        required_map = {"debug": False, "requestid": False}
        for arg in optional or []:
            required_map[arg] = False
        for arg in required or []:
            required_map[arg] = True

        arguments = {}
        for (arg, req) in required_map.items():
            #log.msg("Checking for arg %s with required=%s" % (arg, req))
            if arg not in request.args:
                if req:
                    return defer.fail(ArgumentError(
                        "Missing mandatory argument %s" % arg))
                else:
                    arguments[arg] = None
                    continue
            values = request.args[arg]
            if not isinstance(values, list):  # pragma: no cover
                # FIXME: This should be something that raises a 500
                # (Internal Server Error)... this is handled internally.
                return defer.fail(ArgumentError(
                    "Internal Error: Expected list for %s, got '%s'"
                    % (arg, str(values))))

            value = values[0]
            if arg in parameter_checks or {}:
                try:
                    value = parameter_checks[arg]("--" + arg, value)
                except ArgumentError, err:
                    return defer.fail(err)
            arguments[arg] = value
        return defer.succeed(arguments)

    def format(self, result, request):
        # This method is called to format error messages, and the only format
        # we currently support for those is "raw"
        #style = getattr(self, "output_format", None)
        #if style is None:
        #    style = getattr(request, "output_format", "raw")
        return self.formatter.format("raw", result, request)

    def finishRender(self, result, request):
        if result:
            request.setHeader('content-length', str(len(result)))
            # TODO: When disconnected, why doesn't write() fail?
            request.write(result)
        else:
            request.setHeader('content-length', 0)
        # TODO: As documented in the twisted http module, should
        # instead register a notifyFinish callback to track clients
        # disconnecting.
        if not request._disconnected:
            request.finish()
        if hasattr(request, 'aq_audit_id'):
            if request._disconnected:
                log.msg('Lost client for command #%d.' % request.aq_audit_id)
            log.msg('Command #%d finished.' % request.aq_audit_id)
            delattr(request, 'aq_audit_id')
        return

    def wrapNonInternalError(self, failure, request):
        """This takes care of 'expected' problems, like NotFoundException."""
        r = failure.trap(*ERROR_TO_CODE.keys())
        request.setResponseCode(ERROR_TO_CODE[r])
        formatted = self.format(failure.value, request)
        return self.finishRender(formatted, request)

    # TODO: Something should go into both the logs and back to the client...
    def wrapError(self, failure, request):
        """This is generally the final stop for errors - anything will be
        caught, logged, and a 500 error passed back to the client."""
        msg = failure.getErrorMessage()
        log.msg("Internal Error: %s\nTraceback:\n%s" %
                (msg, failure.getBriefTraceback()))
        #failure.printDetailedTraceback()
        request.setResponseCode(http.INTERNAL_SERVER_ERROR)
        return self.finishRender(msg, request)


class RestServer(ResponsePage):
    """The root resource is used to define the site as a whole."""
    def __init__(self, config):
        formatter = ResponseFormatter()
        ResponsePage.__init__(self, '', formatter)
        self.config = config

        BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
        tree = ET.parse(os.path.join(BINDIR, '..', 'etc', 'input.xml'))

        for command in tree.getiterator("command"):
            for transport in command.getiterator("transport"):
                if "name" not in command.attrib \
                        or "method" not in transport.attrib \
                        or "path" not in transport.attrib:
                    continue
                name = command.attrib["name"]
                method = transport.attrib["method"]
                path = transport.attrib["path"]
                trigger = transport.attrib.get("trigger")

                fullcommand = name
                if trigger:
                    fullcommand = fullcommand + "_" + trigger
                mymodule = getattr(commands, fullcommand, None)
                if not mymodule:
                    log.msg("No module available in aquilon.worker.commands " +
                            "for %s" % fullcommand)
                # See commands/__init__.py for more info here...
                myinstance = getattr(mymodule, "broker_command", None)
                if not myinstance:
                    log.msg("No class instance available for %s" % fullcommand)
                    myinstance = BrokerCommand()
                myinstance.command = name
                rendermethod = method.upper()

                self.insert_instance(myinstance, rendermethod, path, formatter)

                # Since we are parsing input.xml anyway, record the possible
                # parameters...
                for option in command.getiterator("option"):
                    if "name" not in option.attrib:
                        continue
                    option_name = option.attrib["name"]
                    if option_name not in myinstance.optional_parameters:
                        myinstance.optional_parameters.append(option_name)
                    if "type" in option.attrib:
                        paramtype = option.attrib["type"]
                        if paramtype == "int":
                            myinstance.parameter_checks[option_name] = force_int
                        elif paramtype == "float":
                            myinstance.parameter_checks[option_name] = force_float
                        elif paramtype == "boolean" or paramtype == "flag":
                            myinstance.parameter_checks[option_name] = force_boolean
                        elif paramtype == "ipv4":
                            myinstance.parameter_checks[option_name] = force_ipv4
                        elif paramtype == "mac":
                            myinstance.parameter_checks[option_name] = force_mac
                        elif paramtype == "json":
                            myinstance.parameter_checks[option_name] = force_json_dict
                        elif paramtype == "string" or paramtype == "file":
                            # Current twisted can't handle unicode output, so
                            # do not allow non-ASCII input either
                            myinstance.parameter_checks[option_name] = force_ascii
                        elif paramtype == "list":
                            myinstance.parameter_checks[option_name] = force_list
                        elif paramtype == "enum":
                            enumtype = option.attrib["enum"]
                            try:
                                enumclass = StringEnum(enumtype)
                                myinstance.parameter_checks[option_name] = enumclass.from_argument
                            except ValueError, e:
                                log.msg("Unknown Enum: %s" % e)
                        else:  # pragma: no cover
                            log.msg("Warning: unknown option type %s" % paramtype)
                    else:  # pragma: no cover
                        log.msg("Warning: argument type not known for %s.%s" %
                                (myinstance.command, option_name))

                    for format in command.getiterator("format"):
                        if "name" not in format.attrib:
                            log.msg("Warning: incorrect format specification "
                                    "for %s." % myinstance.command)
                            continue

                        style = format.attrib["name"]
                        if hasattr(myinstance.formatter, "config_" + style):
                            meth = getattr(myinstance.formatter, "config_" +
                                           style)
                            meth(format, myinstance.command)

        cache_version(config)
        log.msg("Starting aqd version %s" % config.get("broker", "version"))

        def _logChildren(level, container):
            for (key, child) in container.listStaticEntities():
                log.msg("Resource at level %d for %s [key:%s]"
                        % (level, child.path, key))
                _logChildren(level + 1, child)
            if getattr(container, "dynamic_child", None):
                log.msg("Resource at level %d for %s [dynamic]"
                        % (level, container.dynamic_child.path))
                _logChildren(level + 1, container.dynamic_child)

        #_logChildren(0, self)

    def insert_instance(self, myinstance, rendermethod, path, formatter):
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
                    child = ResponsePage(relative, formatter)
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
                        log.msg("Warning: Could not use variable '"
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
                    child = ResponsePage(relative, formatter,
                                         path_variable=path_variable)
                    container.dynamic_child = child
                    container = child

        if container.handlers.get(rendermethod, None):
            log.msg("Warning: Already have a %s here at %s..." %
                    (rendermethod, container.path))
        #log.msg("Setting 'command_" + fullcommand + "' as '" + rendermethod + "' for container '" + container.path + "'.")
        container.handlers[rendermethod] = myinstance
