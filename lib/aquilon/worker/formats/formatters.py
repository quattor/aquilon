# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
"""Base classes for formatting objects."""

import csv
import sys

from six import text_type
from six.moves import cStringIO as StringIO  # pylint: disable=F0401

import google.protobuf.message
from google.protobuf.descriptor import FieldDescriptor

from aquilon.config import Config
from aquilon.exceptions_ import ProtocolError
from aquilon.worker.processes import build_mako_lookup

# Note: the built-in "excel" dialect uses '\r\n' for line ending and that breaks
# the tests.
csv.register_dialect('aquilon', delimiter=',', quoting=csv.QUOTE_MINIMAL,
                     doublequote=True, lineterminator='\n')


class ResponseFormatter(object):
    """This handles the top level of formatting results... results
        pass through here and are delegated out to ObjectFormatter
        handlers and wrapped appropriately.

    """
    formats = ["raw", "csv", "proto", "djb"]

    loaded_protocols = {}

    def __init__(self):
        self.protobuf_container = None

    def config_proto(self, node, command):
        desc_node = node.find("message_class")
        if desc_node is None or "name" not in desc_node.attrib or \
           "module" not in desc_node.attrib:  # pragma: no cover
            raise ProtocolError("Invalid protobuf definition for %s." % command)

        module = desc_node.attrib["module"]
        msgclass = desc_node.attrib["name"]

        if module in self.loaded_protocols and \
           self.loaded_protocols[module] is False:  # pragma: no cover
            raise ProtocolError("Protocol %s: previous import attempt was "
                                "unsuccessful" % module)

        if module not in self.loaded_protocols:
            config = Config()
            protodir = config.get("protocols", "directory")

            # Modifying sys.path here is ugly. We could try playing with
            # find_module()/load_module(), but there are dependencies between
            # the protocols, that could fail if sys.path is not set up and the
            # protocols are loaded in the wrong order.
            if protodir not in sys.path:
                sys.path.append(protodir)

            try:
                self.loaded_protocols[module] = __import__(module)
            except ImportError as err:  # pragma: no cover
                self.loaded_protocols[module] = False
                raise ProtocolError("Protocol %s: %s" % (module, err))

        self.protobuf_container = getattr(self.loaded_protocols[module],
                                          msgclass)

        # The formatter code assumes that the output message type has a single,
        # repeated field only. Verify that assumption here, to ease the
        # debugging of invalid protocol definitions.
        descriptor = self.protobuf_container.DESCRIPTOR
        if len(descriptor.fields) != 1:  # pragma: no cover
            raise ProtocolError("%s: The formatter code needs a message type "
                                "which has a single, repeated field only." %
                                descriptor.full_name)

        field = descriptor.fields[0]
        if field.label != FieldDescriptor.LABEL_REPEATED:  # pragma: no cover
            raise ProtocolError("%s: The single field inside the output "
                                "message type must be repeated." %
                                field.full_name)

    def format(self, style, result, request):
        """The main entry point - it is expected that any consumers call
            this method and let the magic happen.

        """
        # TODO: add Content-Type/Content-Transfer-Encoding headers
        m = getattr(self, "format_" + str(style).lower(), self.format_raw)
        return m(result, request)

    def format_raw(self, result, request):
        # Shortcut for text result
        if isinstance(result, text_type):
            return result.encode("utf-8")
        return ObjectFormatter.redirect_raw(result,
                                            embedded=False).encode("utf-8")

    def format_csv(self, result, request):
        strbuf = StringIO()
        writer = csv.writer(strbuf, dialect='aquilon')
        ObjectFormatter.redirect_csv(result, writer)
        return strbuf.getvalue().encode("utf-8")

    def format_djb(self, result, request):
        """ For tinydns-data formatting. use raw for now. """
        return ObjectFormatter.redirect_djb(result).encode("utf-8")

    def format_proto(self, result, request):
        if not self.protobuf_container:  # pragma: no cover
            raise ProtocolError("Protobuf formatter is not available")

        # Here, we rely on the message type returned by any commands being a
        # list, which should always have just one, repeated field. These
        # assumptions are verified in the config_proto() method when the
        # protocol is loaded.
        container = self.protobuf_container()
        field_name = container.DESCRIPTOR.fields[0].name
        ObjectFormatter.redirect_proto(result, getattr(container, field_name),
                                       embedded=False)
        return container.SerializeToString()


class ObjectFormatter(object):
    """This class and its subclasses are meant to do the real work of
        formatting individual objects.  The standard instance methods
        do the heavy lifting, which the static methods allow for
        delegation when needed.

        The instance methods (format_*) provide default implementations,
        but it is expected that they will be overridden to provide more
        useful information.
     """

    config = Config()

    handlers = {}

    """ The handlers dictionary should have an entry for every subclass.
        Typically this will be defined immediately after defining the
        subclass.

    """

    # Be careful about using the module_directory and cache!
    # Not using module_directory so that we don't have to worry about stale
    # files hanging around on upgrade.  Race conditions in writing the files
    # might also be an issue when we switch to multi-process.
    # Not using cache because it only has the lifetime of the template, and
    # because we do not have the beaker module installed.
    lookup_raw = build_mako_lookup(config, "raw",
                                   imports=['from string import rstrip',
                                            'from aquilon.worker.formats.formatters import shift'],
                                   default_filters=['unicode', 'rstrip'])

    # Pass embedded=False if this is the top-level object being rendered.
    # Pass indirect_attrs=False to prevent loading expensive collection-based
    # attributes.
    def format_raw(self, result, indent="", embedded=True,
                   indirect_attrs=True):
        if hasattr(self, "template_raw"):
            template = self.lookup_raw.get_template(self.template_raw)
            return shift(template.render(record=result, formatter=self),
                         indent=indent).rstrip()
        return indent + str(result)

    def csv_fields(self, result):  # pragma: no cover
        raise ProtocolError("{0!r} does not have a CSV formatter."
                            .format(type(result)))

    def format_csv(self, result, writer):
        for fields in self.csv_fields(result):
            if fields:
                writer.writerow(fields)

    def format_djb(self, result):
        # We get here if the command throws an exception
        return self.format_raw(result)

    # Pass embedded=False if this is the top-level object being rendered.
    # Pass indirect_attrs=False to prevent loading expensive collection-based
    # attributes.
    def format_proto(self, result, container, embedded=True,
                     indirect_attrs=True):
        # Here, container can be either a repeated field, in which case we need
        # to call .add() to instantiate a new message, or a singular (either
        # required or optional) field, in which case it can be used as a message
        # directly.
        #
        # The first case happens e.g. for all "show" commands that return a
        # single object only. Since we always return a list of messages when
        # protobuf format is used, we need the implicit object -> list
        # conversion here.
        #
        # The second case happens all the time when self.redirect_proto() is
        # used.
        if isinstance(container, google.protobuf.message.Message):
            # Singular field
            skeleton = container
        else:
            # Repeated field; we're implicitly converting the result object to a
            # list of length 1
            skeleton = container.add()

        self.fill_proto(result, skeleton, embedded=embedded,
                        indirect_attrs=indirect_attrs)

    def fill_proto(self, result, skeleton, embedded=True, indirect_attrs=True):  # pragma: no cover
        # pylint: disable=W0613
        # There's no default protobuf message type
        raise ProtocolError("{0!r} does not have a protobuf formatter."
                            .format(type(result)))

    @staticmethod
    def redirect_raw(result, indent="", embedded=True, indirect_attrs=True):
        handler = ObjectFormatter.handlers.get(result.__class__,
                                               ObjectFormatter.default_handler)
        return handler.format_raw(result, indent, embedded=embedded,
                                  indirect_attrs=indirect_attrs)

    @staticmethod
    def redirect_csv(result, writer):
        handler = ObjectFormatter.handlers.get(result.__class__,
                                               ObjectFormatter.default_handler)
        return handler.format_csv(result, writer)

    @staticmethod
    def redirect_djb(result):
        handler = ObjectFormatter.handlers.get(result.__class__,
                                               ObjectFormatter.default_handler)
        return handler.format_djb(result)

    @staticmethod
    def redirect_proto(result, container, embedded=True, indirect_attrs=True):
        handler = ObjectFormatter.handlers.get(result.__class__,
                                               ObjectFormatter.default_handler)
        handler.format_proto(result, container, embedded=embedded,
                             indirect_attrs=indirect_attrs)

ObjectFormatter.default_handler = ObjectFormatter()


# Convenience method for mako templates
def shift(result, indent="  "):
    return "\n".join("%s%s" % (indent, line) for line in result.splitlines())
