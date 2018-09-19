# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018  Contributor
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
match the available format functions.  A request for location.proto,
for example, will retrieve 'location' and format it with format_proto().

ToDo:
    - Add some sort of interface that can be implemented for
        objects to give hints on how they should be rendered.
    - Add other output formats (csv, xml, etc.).

"""

import re
from xml.etree import ElementTree

from six import iteritems

from twisted.web import server, resource, http
from twisted.internet import defer, threads
from twisted.python import log, context
from twisted.python.log import ILogContext

from aquilon.config import lookup_file_path
from aquilon.aqdb.types import StringEnum
from aquilon.exceptions_ import ArgumentError, ProtocolError
from aquilon.worker.formats.formatters import ResponseFormatter
from aquilon.worker.broker import BrokerCommand, ERROR_TO_CODE
from aquilon.worker import commands
from aquilon.worker.processes import cache_version
from aquilon.worker.messages import StatusCatalog
from aquilon.utils import (force_int, force_float, force_boolean, force_ip,
                           force_mac, force_ascii, force_list, force_json,
                           force_uuid)
from aquilon.worker.command_registry import CommandRegistry, CommandEntry

# Regular Expression for matching variables in a path definition.
# Currently only supports stuffing a single variable in a path
# component.
varmatch = re.compile(r'^%\((.*)\)s$')

catalog = StatusCatalog()


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
            # log.msg("Checking style: %s" % style)
            extension = "." + style
            if path.endswith(extension):
                # log.msg("Retrieving formatted child for dynamic page: %s" % path)
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

        # log.msg("Retrieving child for dynamic page: %s" % path)
        request.args[self.dynamic_child.path_variable] = [path]
        return self.dynamic_child

    def extractArguments(self, request):
        result = {}
        for arg, values in iteritems(request.args):
            try:
                # Parameter names should be plain ASCII
                arg = arg.decode("ascii")
            except UnicodeError:
                raise ProtocolError("Non-ASCII command parameter")

            if not isinstance(values, list):  # pragma: no cover
                raise ProtocolError("Expected list for %s, got %s"
                                    % (arg, type(values)))
            if len(values) > 1:
                raise ProtocolError("Too many values specified for %s"
                                    % arg)

            try:
                result[arg] = values[0].decode("utf-8")
            except UnicodeError:
                raise ProtocolError("Value for parameter %s is not "
                                    "valid UTF-8" % arg)
        return result

    def render(self, request):
        """This is based on the default implementation from
        resource.Resource that checks for the appropriate method to
        delegate to.

        It adds a default handler for arguments in a PUT request and
        delegation of argument parsing.
        The processing is pushed off onto a thread and wrapped with
        error handling.

        """
        if request.method == b'PUT':
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

        # Retieve the instance from the handler and hook up the logger
        broker_command = handler.broker_command
        request.logger.add_command_handler(broker_command.module_logger)

        # Process requestid early, so we can keep track of the request even if
        # parsing the rest of the arguments fail
        if b"requestid" in request.args:
            requestid = force_uuid("--requestid",
                                   request.args[b"requestid"][0].decode("ascii"))
        else:
            requestid = None

        # For the show_request command, requestid is the UUID of the command we
        # want to monitor and not the UUID of this command. As a result,
        # show_request commands do not have a requestid in request.status.
        # For other commands, adding the requestid to the catalog here means
        # that any matching show_request commands will notice any errors which
        # happen after this point
        if broker_command.command != "show_request":
            requestid = catalog.store_requestid(request.status, requestid)

        # Create a defered chain of actions (or continuation Mondad).  We add
        # a list of the functions that should be called, and error handeling
        # At the end of this block we will invoke the monad with the request
        d = defer.Deferred()

        # Using callbacks here is a bit of a stretch since these calls are not
        # asynchronous, but it means exceptions will be caught and reported as
        # expected to the client without any extra effort
        d.addCallback(self.extractArguments)
        d.addCallback(handler.check_arguments)

        style = getattr(self, "output_format", None)
        if style is None:
            style = getattr(request, "output_format", None)
        if style is None:
            style = getattr(broker_command, "default_style", "raw")

        # Prepare for command execution: add synthetic arguments and log the
        # request
        d = d.addCallback(lambda arguments:
                          broker_command.pre_render(request, requestid,
                                                    style=style,
                                                    **arguments))
        if broker_command.defer_to_thread:
            d = d.addCallback(lambda arguments: threads.deferToThread(
                broker_command.invoke_render, **arguments))

            # Save the current log context, as it does not survive deferring
            # execution to a thread
            ctx = context.get(ILogContext)
            d = d.addBoth(self.restoreContext, ctx)
        else:
            d = d.addCallback(lambda arguments: broker_command.invoke_render(**arguments))
        d = d.addCallback(self.finishRender, request)
        d = d.addErrback(self.logFailure, request)
        d = d.addErrback(self.wrapNonInternalError, request)
        d = d.addErrback(self.wrapError, request)
        d.callback(request)
        return server.NOT_DONE_YET

    def format(self, result, request):
        # This method is called to format error messages, and the only format
        # we currently support for those is "raw"
        # style = getattr(self, "output_format", None)
        # if style is None:
        #     style = getattr(request, "output_format", "raw")
        return self.formatter.format("raw", result, request)

    def restoreContext(self, result, ctx):
        context.get(ILogContext).update(ctx)

        # Pass through
        return result

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
        else:
            log.msg('Lost client for command #%d.' % request.sequence_no)
        log.msg('Command #%d finished.' % request.sequence_no)
        return

    def logFailure(self, failure, request):
        request.logger.info("%s: %s", type(failure.value).__name__, failure.value)

        # Pass through
        return failure

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
        # failure.printDetailedTraceback()
        request.setResponseCode(http.INTERNAL_SERVER_ERROR)
        request.setHeader("Content-Type", "text/plain; charset=utf-8")
        return self.finishRender(msg.encode("utf-8"), request)


class RestServer(ResponsePage):
    """The root resource is used to define the site as a whole."""

    def __init__(self, config):
        formatter = ResponseFormatter()
        ResponsePage.__init__(self, '', formatter)
        self.config = config

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

        # _logChildren(0, self)

    def insert_handler(self, handler, rendermethod, path):
        container = self
        relative = ""
        # Traverse down the resource tree, container will
        # end up pointing to the correct spot.
        # Create branches and leaves as necessary, continueing to
        # traverse downward.
        for component in path.split("/"):
            relative = relative + "/" + component
            # log.msg("Working with component '" + component + "' of '" + relative + "'.")
            m = varmatch.match(component)
            # Is this piece of the path dynamic?
            if not m:
                # log.msg("Component '" + component + "' is static.")
                child = container.getStaticEntity(component)
                if child is None:
                    # log.msg("Creating new static component '" + component + "'.")
                    child = ResponsePage(relative, self.formatter)
                    container.putChild(component, child)
                container = child
            else:
                # log.msg("Component '" + component + "' is dynamic.")
                path_variable = m.group(1)
                if container.dynamic_child is not None:
                    # log.msg("Dynamic component '" + component + "' already exists.")
                    current_variable = container.dynamic_child.path_variable
                    if current_variable != path_variable:
                        log.msg("Warning: Could not use variable '"
                                + path_variable + "', already have "
                                + "dynamic variable '"
                                + current_variable + "'.")
                        # XXX: Raise an error if they don't match
                        container = container.dynamic_child
                    else:
                        # log.msg("Dynamic component '" + component + "' had correct variable.")
                        container = container.dynamic_child
                else:
                    # log.msg("Creating new dynamic component '" + component + "'.")
                    child = ResponsePage(relative, self.formatter,
                                         path_variable=path_variable)
                    container.dynamic_child = child
                    container = child

        if container.handlers.get(rendermethod, None):
            log.msg("Warning: Already have a %s here at %s..." %
                    (rendermethod, container.path))
        # log.msg("Setting 'command_" + fullcommand + "' as '" + rendermethod + "' for container '" + container.path + "'.")
        container.handlers[rendermethod] = handler

###############################################################################

class ResourcesCommandEntry(CommandEntry):

    _type_handler = {
        'int': force_int,
        'float': force_float,
        'boolean': force_boolean,
        'flag': force_boolean,
        'ip': force_ip,
        'mac': force_mac,
        'json': force_json,
        'string': force_ascii,
        'file': force_ascii,
        'list': force_list,
        'uuid': force_uuid,
    }

    def __init__(self, fullname, method, path, name, trigger):
        super(ResourcesCommandEntry, self).__init__(fullname, method, path, name, trigger)

        # Locate the instance of the BrokerCommand
        # See commands/__init__.py for more info here...
        broker_module = getattr(commands, fullname, None)
        if not broker_module:
            log.msg("No module available in aquilon.worker.commands " +
                    "for %s" % fullname)
        broker_command = getattr(broker_module, "broker_command", None)
        if not broker_command:
            log.msg("No class instance available for %s" % fullname)
            broker_command = BrokerCommand()

        # Save the broker command for later usage
        self.broker_command = broker_command

        # Update the shortname of the command
        broker_command.command = name

        # HTTP GET should only be used for queries, so force such commands to be
        # read-only and require using the formatters.
        if method.lower() == "get":
            if not broker_command.requires_readonly:
                log.msg("Command %s uses GET, setting it to read-only" %
                        fullname)
            broker_command.requires_readonly = True

            # show_request must be able to override requires_format to False
            if broker_command.requires_format is None:
                broker_command.requires_format = True

        # Fill in the required arguments from the instance of BrokerComamnd
        # this will be extended when more options are found in add_option.
        self.argument_requirements = {"debug": False, "requestid": False}
        for arg in broker_command.optional_parameters:
            self.argument_requirements[arg] = False
        for arg in broker_command.required_parameters:
            self.argument_requirements[arg] = True

        # Checks for specific parameters, filled in by add_option
        self.parameter_checks = {}

    def add_option(self, option_name, paramtype, enumtype=None):
        # If this argument was not specified directly by the instance of
        # BrokerCommand then record it as optional (FIXME)
        if option_name not in self.argument_requirements:
            self.argument_requirements[option_name] = False

        # Fill in the parameter checker for this option
        if paramtype == 'enum':
            if not enumtype:
                log.msg("Warning: argument missing enum attribute for %s.%s" %
                        (self.broker_command.command, option_name))
                return
            try:
                enum_class = StringEnum(enumtype)
                self.parameter_checks[option_name] = enum_class.from_argument
            except ValueError as e:
                log.msg("Unknown Enum: %s" % e)
                return
        else:
            if paramtype in self._type_handler:
                self.parameter_checks[option_name] = self._type_handler[paramtype]
            else:
                log.msg("Warning: unknown option type %s for %s.%s" %
                        (paramtype, self.broker_command.command, option_name))

    def check_arguments(self, arguments):
        """Check for the required and optional arguments.

        Returns a dictionary of the arguments found.  Any unsupplied optional
        arguments will have a value of None.  If there are any problems an
        exception will be raised.

        """
        result = {}
        for arg, req in self.argument_requirements.items():
            # log.msg("Checking for arg %s with required=%s" % (arg, req))
            if arg not in arguments:
                if req:
                    raise ArgumentError("Missing mandatory argument %s" % arg)
                elif arg != "requestid":
                    result[arg] = None
                    continue

            # requestid was already parsed, and will be re-injected to the
            # argument list later
            if arg == "requestid":
                continue

            value = arguments[arg]
            if arg in self.parameter_checks:
                value = self.parameter_checks[arg]("--" + arg, value)
            result[arg] = value
        return result

    def add_format(self, format, style):
        # If input.xml specifies a format description, then we need to go
        # through the formatter
        self.broker_command.requires_format = True

        if hasattr(self.broker_command.formatter, "config_" + style):
            meth = getattr(self.broker_command.formatter, "config_" + style)
            meth(format, self.broker_command.command)


class ResourcesCommandRegistry(CommandRegistry):
    def __init__(self, server):
        # Save the additional instance of ResourceServer and call
        # the base class to finish setting up.
        self.server = server
        super(ResourcesCommandRegistry, self).__init__()

    def new_entry(self, fullname, method, path, name, trigger):
        # Create a new instance of ResourcesCommandEntry.  It's add_option
        # and add_format methods will get called to populate the entry.
        return ResourcesCommandEntry(fullname, method, path, name, trigger)

    def add_entry(self, entry):
        # Once the ResourcesCommandEntry has been populated this method
        # is called.  We insert the entry into the ResourceServer to
        # expose them.
        self.server.insert_handler(entry, entry.method.upper(), entry.path)
