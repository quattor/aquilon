#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
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

from twisted.application import internet
from twisted.web import server, resource, http, error, static
from twisted.internet import defer, utils, threads
from twisted.python import log

from aquilon.exceptions_ import ArgumentError, AuthorizationException, \
        NotFoundException
from aquilon.server.formats import Formatter

class ResponsePage(resource.Resource):

    def __init__(self, broker, path, formatter, path_variable=None):
        self.path = path
        self.broker = broker
        self.path_variable = path_variable
        self.dynamic_child = None
        resource.Resource.__init__(self)
        self.formatter = formatter

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
        """This is just the default implementation from resource.Resource
        that checks for the appropriate method to delegate to.  This can
        be expanded out to do any default/incoming processing...

        One possibility would be for it to simplify request.args to
        have another value, maybe request.simple_args that decomposed
        single-element lists back to single variables.

        """
        if request.method == 'PUT':
            # For now, assume all put requests use a simple urllib encoding.
            request.content.seek(0)
            # Since these are both lists, there is a theoretical case where
            # one might want to merge the lists, instead of overwriting with
            # the new.  Not sure if that matters right now.
            request.args.update( http.parse_qs(request.content.read()) )
        m = getattr(self, 'render_' + request.method, None)
        if not m:
            raise server.UnsupportedMethod(getattr(self, 'allowedMethods', ()))
        return m(request)

    def check_arguments(self, request, required = [], optional = []):
        """Check for the required and optional arguments.

        Returns a Deferred that will have a dictionary of the arguments
        found.  Any unsupplied optional arguments will have a value of 
        None.  If there are any problems, the Deferred will errback with
        a failure.
        
        This should probably rely on the input.xml file for the list
        of required and optional arguments.  For now, it is just a 
        utility function.
        """

        required_map = {}
        for arg in optional or []:
            required_map[arg] = False
        for arg in required or []:
            required_map[arg] = True

        arguments = {}
        for (arg, req) in required_map.items():
            if not request.args.has_key(arg):
                if req:
                    return defer.fail(ArgumentError(
                        "Missing mandatory argument %s" % arg))
                else:
                    arguments[arg] = None
                    continue
            values = request.args[arg]
            if not isinstance(values, list):
                # FIXME: This should be something that raises a 500
                # (Internal Server Error)... this is handled internally.
                return defer.fail(ArgumentError(
                    "Internal Error: Expected list for %s, got '%s'"
                    % (arg, str(values))))
            arguments[arg] = values[0]
        return defer.succeed(arguments)

    def format(self, result, request):
        style = getattr(self, "output_format", None)
        if style is None:
            style = getattr(request, "output_format", "raw")
        return self.formatter.format(style, result, request)

    def finishRender(self, result, request):
        if result:
            request.setHeader('content-length', str(len(result)))
            request.write(result)
        else:
            request.setHeader('content-length', 0)
        request.finish()
        return

    def finishOK(self, result, request):
        """Ignore any results - usually empty for this - and finish"""
        return self.finishRender("", request)

    def wrapNonInternalError(self, failure, request):
        """This takes care of 'expected' problems, like NotFoundException."""
        r = failure.trap(NotFoundException, AuthorizationException,
                ArgumentError)
        if r == NotFoundException:
            request.setResponseCode(http.NOT_FOUND)
        elif r == AuthorizationException:
            request.setResponseCode(http.UNAUTHORIZED)
        elif r == ArgumentError:
            request.setResponseCode(http.BAD_REQUEST)
        formatted = self.format(failure.value, request)
        return self.finishRender(formatted, request)

    # TODO: Something should go into both the logs and back to the client...
    def wrapError(self, failure, request):
        """This is generally the final stop for errors - anything will be
        caught, logged, and a 500 error passed back to the client."""
        log.err(failure.getBriefTraceback())
        msg = failure.getErrorMessage()
        log.err(failure.getErrorMessage())
        #failure.printDetailedTraceback()
        request.setResponseCode(http.INTERNAL_SERVER_ERROR)
        return self.finishRender(msg, request)

    def format_or_fail(self, d, request):
        """Utility method for finishing a request that needs to be formatted."""
        d = d.addCallback(self.format, request)
        d = d.addCallback(self.finishRender, request)
        d = d.addErrback(self.wrapNonInternalError, request)
        d = d.addErrback(self.wrapError, request)
        return server.NOT_DONE_YET

    def finish_or_fail(self, d, request):
        """Utility method for finishing up a request that produces no output."""
        d = d.addCallback(self.finishOK, request)
        d = d.addErrback(self.wrapNonInternalError, request)
        d = d.addErrback(self.wrapError, request)
        return server.NOT_DONE_YET

    def command_show_host_all(self, request):
        """aqcommand: aq show host --all"""
        d = self.check_arguments(request)
        d = d.addCallback(self.broker.show_host_all,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_show_host_hostname(self, request):
        """aqcommand: aq show host --hostname=<host>"""
        d = self.check_arguments(request, ["hostname"])
        d = d.addCallback(self.broker.show_host,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_add_host(self, request):
        """aqcommand: aq add host --hostname=<host>"""
        d = self.check_arguments(request,
                ["hostname", "machine", "domain", "status"])
        d = d.addCallback(self.broker.add_host,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_del_host(self, request):
        """aqcommand: aq del host --hostname=<host>"""
        d = self.check_arguments(request, ["hostname"])
        d = d.addCallback(self.broker.del_host,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

    def command_assoc(self, request):
        """aqcommand: aq assoc --hostname=<host>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq assoc has not been implemented yet"

    def command_reconfigure(self, request):
        """aqcommand: aq reconfigure --hostname=<host>"""
        d = self.check_arguments(request, ["hostname"])
        d = d.addCallback(self.broker.reconfigure,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

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
        d = self.check_arguments(request, ["domain"])
        d = d.addCallback(self.broker.add_domain,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

    def command_del_domain(self, request):
        """aqcommand: aq del domain --domain=<domain>"""
        d = self.check_arguments(request, ["domain"])
        d = d.addCallback(self.broker.del_domain,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

    def command_add_template(self, request):
        """aqcommand: aq add template --name=<name> --domain=<domain>"""
        domain = request.args['domain'][0]
        template = request.args['name'][0]

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add_template has not been implemented yet"

    def command_get(self, request):
        """aqcommand: aq get"""

        request.args["domain"] = [self.broker.domain_name]

        return self.command_get_domain(request)

    def command_get_domain(self, request):
        """aqcommand: aq get --domain=<domain>"""
        d = self.check_arguments(request, ["domain"])
        d = d.addCallback(self.broker.get,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_put(self, request):
        """aqcommand: aq put --domain=<domain>"""
        d = self.check_arguments(request, ["domain", "bundle"])
        d = d.addCallback(self.broker.put,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

    def command_deploy(self, request):
        """aqcommand: aq deploy --domain=<domain> --to=<domain>"""
        d = self.check_arguments(request, ["domain"], ["to"])
        d = d.addCallback(self.broker.deploy,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

    def command_manage(self, request):
        """aqcommand: aq manage --hostname=<name> --domain=<domain>"""
        d = self.check_arguments(request, ["hostname", "domain"])
        d = d.addCallback(self.broker.manage,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

    def command_sync(self, request):
        """aqcommand: aq sync"""

        # FIXME: This should be the user's current domain, as set by aq config.
        request.args["domain"] = [self.broker.domain_name]

        return self.command_sync_domain(request)

    def command_sync_domain(self, request):
        """aqcommand: aq sync --domain=<domain>"""
        d = self.check_arguments(request, ["domain"])
        d = d.addCallback(self.broker.sync,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_show_location_types(self, request):
        """aqcommand: aq show location"""
        d = self.check_arguments(request)
        d = d.addCallback(self.broker.show_location_type,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_show_location_type(self, request):
        """aqcommand: aq show location --type"""
        d = self.check_arguments(request, ["type"])
        d = d.addCallback(self.broker.show_location,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_show_location_name(self, request):
        """aqcommand: aq show location --name=<location>"""
        d = self.check_arguments(request, ["type", "name"])
        d = d.addCallback(self.broker.show_location,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_add_location(self, request):
        """aqcommand: aq add location --locationname=<location>"""
        d = self.check_arguments(request,
                ["type", "name", "parenttype", "parentname"],
                ["fullname", "comments"])
        d = d.addCallback(self.broker.add_location,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_del_location(self, request):
        """aqcommand: aq del location --type=<type> --name=<name>"""
        d = self.check_arguments(request, ["type", "name"])
        d = d.addCallback(self.broker.del_location,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

    def command_add_chassis(self, request):
        request.args['type'] = ['chassis']
        request.args['parenttype'] = ['rack']
        request.args['parentname'] = request.args['rack']
        return self.command_add_location(request)

    def command_show_chassis(self, request):
        request.args["type"] = ["chassis"]
        return self.command_show_location_type(request)

    def command_show_chassis_name(self, request):
        request.args["type"] = ["chassis"]
        return self.command_show_location_name(request)

    def command_del_chassis(self, request):
        request.args["type"] = ["chassis"]
        return self.command_del_location(request)

    def command_add_rack(self, request):
        request.args['type'] = ['rack']
        request.args['parenttype'] = ['building']
        request.args['parentname'] = request.args['building']
        return self.command_add_location(request)

    def command_show_rack(self, request):
        request.args["type"] = ["rack"]
        return self.command_show_location_type(request)

    def command_show_rack_name(self, request):
        request.args["type"] = ["rack"]
        return self.command_show_location_name(request)

    def command_del_rack(self, request):
        request.args["type"] = ["rack"]
        return self.command_del_location(request)

    def command_add_building(self, request):
        request.args['type'] = ['building']
        request.args['parenttype'] = ['city']
        request.args['parentname'] = request.args['city']
        return self.command_add_location(request)

    def command_show_building(self, request):
        request.args["type"] = ["building"]
        return self.command_show_location_type(request)

    def command_show_building_name(self, request):
        request.args["type"] = ["building"]
        return self.command_show_location_name(request)

    def command_del_building(self, request):
        request.args["type"] = ["building"]
        return self.command_del_location(request)

    def command_add_city(self, request):
        request.args["type"] = ["city"]
        request.args["parenttype"] = ["country"]
        request.args["parentname"] = request.args["country"]
        return self.command_add_location(request)

    def command_show_city(self, request):
        request.args["type"] = ["city"]
        return self.command_show_location_type(request)

    def command_show_city_name(self, request):
        request.args["type"] = ["city"]
        return self.command_show_location_name(request)

    def command_del_city(self, request):
        request.args["type"] = ["city"]
        return self.command_del_location(request)

    def command_add_country (self, request):
        request.args["type"] = ["country"]
        request.args["parenttype"] = ["continent"]
        request.args["parentname"] = request.args["continent"]
        return self.command_add_location(request)

    def command_show_country(self, request):
        request.args["type"] = ["country"]
        return self.command_show_location_type(request)

    def command_show_country_name(self, request):
        request.args["type"] = ["country"]
        return self.command_show_location_name(request)

    def command_del_country(self, request):
        request.args["type"] = ["country"]
        return self.command_del_location(request)

    def command_add_continent (self, request):
        request.args["type"] = ["continent"]
        request.args["parenttype"] = ["hub"]
        request.args["parentname"] = request.args["hub"]
        return self.command_add_location(request)

    def command_show_continent(self, request):
        request.args["type"] = ["continent"]
        return self.command_show_location_type(request)

    def command_show_continent_name(self, request):
        request.args["type"] = ["continent"]
        return self.command_show_location_name(request)

    def command_del_continent(self, request):
        request.args["type"] = ["continent"]
        return self.command_del_location(request)

    def command_add_hub (self, request):
        request.args["type"] = ["hub"]
        request.args["parenttype"] = ["company"]
        request.args["parentname"] = "ms" 
        return self.command_add_location(request)

    def command_show_hub(self, request):
        request.args["type"] = ["hub"]
        return self.command_show_location_type(request)

    def command_show_hub_name(self, request):
        request.args["type"] = ["hub"]
        return self.command_show_location_name(request)

    def command_del_hub(self, request):
        request.args["type"] = ["hub"]
        return self.command_del_location(request)

    def command_status(self, request):
        """aqcommand: aq status"""
        d = self.check_arguments(request)
        d = d.addCallback(self.broker.status,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_add_cpu (self, request):
        """aqcommand add cpu --name name --vedor vendor --speed speed"""
        d = self.check_arguments(request, ['name', 'vendor', 'speed'])
        d = d.addCallback(self.broker.add_cpu,
            request_path=request.path,
            user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)
    
    def command_add_disk (self, request):
        """aqcommand add disk --machine machine --type type --capacity capacity"""
        d = self.check_arguments(request, ['machine', 'type', 'capacity'])
        d = d.addCallback(self.broker.add_disk,
            request_path=request.path,
            user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)
    
    def command_add_hardware(self, request):
        """aqcommand: aq add hardware --location=<location>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add hardware has not been implemented yet"

    def command_add_service(self, request):
        d = self.check_arguments(request, ['service'], ['instance'])
        d = d.addCallback(self.broker.add_service,
                request_path = request.path,
                user = request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_add_service_instance(self, request):
        d = self.check_arguments(request, ['service', 'instance'])
        d = d.addCallback(self.broker.add_service,
                request_path = request.path,
                user = request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_show_service(self, request):
        d = self.check_arguments(request, [], ['service'])
        d = d.addCallback(self.broker.show_service,
                request_path = request.path,
                user = request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_show_service_service(self, request):
        d = self.check_arguments(request, ['service'])
        d = d.addCallback(self.broker.show_service,
                request_path = request.path,
                user = request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_del_service(self, request):
        d = self.check_arguments(request, ['service'], ['instance'])
        d = d.addCallback(self.broker.del_service,
                request_path = request.path,
                user = request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

    def command_del_service_instance(self, request):
        d = self.check_arguments(request, ['service', 'instance'])
        d = d.addCallback(self.broker.del_service,
                request_path = request.path,
                user = request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

    def command_bind_service(self, request):
        d = self.check_arguments(request, ['hostname', 'service', 'instance'])
        d = d.addCallback(self.broker.bind_service,
                request_path = request.path,
                user = request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_unbind_service(self, request):
        d = self.check_arguments(request, ['hostname', 'service', 'instance'])
        d = d.addCallback(self.broker.unbind_service,
                request_path = request.path,
                user = request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_make_aquilon(self, request):
        """aqcommand: aq make aquilon --hostname=<name> --os=<os>
            [--personality=<personality>]"""
        d = self.check_arguments(request, ["hostname", "os"], ["personality"])
        d = d.addCallback(self.broker.make_aquilon,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

    def command_add_model(self, request):
        d = self.check_arguments(request,
                ["name", "vendor", "type"],
                ["cputype","cpunum","mem","disktype","disksize","nics"])
        d = d.addCallback(self.broker.add_model,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_show_model(self, request):
        d = self.check_arguments(request, [],
                ["name", "vendor", "type"])
        d = d.addCallback(self.broker.show_model,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.format_or_fail(d, request)
    
    def command_del_model(self, request):
        d = self.check_arguments(request,
                ["name", "vendor", "hardware"])
        d = d.addCallback(self.broker.del_model,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_pxeswitch(self, request):
        d = self.check_arguments(request, ["hostname"], ["boot", "install"])
        d = d.addCallback(self.broker.pxeswitch,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

    def command_add_machine(self, request):
        d = self.check_arguments(request,
                ["machine", "location", "type", "model", 
                    "cpuname", "cpuvendor", "cpuspeed", "cpucount", "memory"],
                ["serial"])
        d = d.addCallback(self.broker.add_machine,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

    def command_show_machine_machine(self, request):
        return self.command_show_machine(request)

    def command_show_machine(self, request):
        d = self.check_arguments(request,
                optional=["machine", "location", "type", "model"])
        d = d.addCallback(self.broker.show_machine,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.format_or_fail(d, request)

    def command_del_machine(self, request):
        d = self.check_arguments(request, ["machine"])
        d = d.addCallback(self.broker.del_machine,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

    def command_add_interface (self, request):
        d = self.check_arguments(request, ["interface", "machine", "mac"],
                ['ip'])
        d = d.addCallback(self.broker.add_interface,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

    def command_del_interface (self, request):
        d = self.check_arguments(request, optional=["interface", "machine", "mac", "ip"])
        d = d.addCallback(self.broker.del_interface,
                request_path=request.path,
                user=request.channel.getPrinciple())
        return self.finish_or_fail(d, request)

#==============================================================================

class RestServer(ResponsePage):
    """The root resource is used to define the site as a whole."""
    def __init__(self, broker):
        formatter = Formatter()
        ResponsePage.__init__(self, broker, '', formatter)

        # Regular Expression for matching variables in a path definition.
        # Currently only supports stuffing a single variable in a path
        # component.
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
                            child = ResponsePage(self.broker, relative,
                                    formatter)
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
                            child = ResponsePage(self.broker, relative,
                                    formatter, path_variable=path_variable)
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

        # Serve up a static templates directory for git...
        #log.msg("Checking on %s" % self.broker.templatesdir)
        if os.path.exists(self.broker.templatesdir):
            self.putChild("templates", static.File(self.broker.templatesdir))
        else:
            log.err("ERROR: templates directory '%s' not found, will not serve"
                    % self.broker.templatesdir)

        def _logChildren(level, container):
            for (key, child) in container.listStaticEntities():
                log.msg("Resource at level %d for %s [key:%s]"
                        % (level, child.path, key))
                _logChildren(level+1, child)
            if getattr(container, "dynamic_child", None):
                log.msg("Resource at level %d for %s [dynamic]"
                        % (level, container.dynamic_child.path))
                _logChildren(level+1, container.dynamic_child)

        #_logChildren(0, self)

