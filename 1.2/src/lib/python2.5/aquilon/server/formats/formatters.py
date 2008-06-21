#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Base classes for formatting objects."""


class ResponseFormatter(object):
    """This handles the top level of formatting results... results
        pass through here and are delegated out to ObjectFormatter
        handlers and wrapped appropriately.

    """
    formats = ["raw", "csv", "html"]

    def format(self, style, result, request):
        """The main entry point - it is expected that any consumers call
            this method and let the magic happen.

        """
        m = getattr(self, "format_" + str(style).lower(), self.format_raw)
        return str(m(result, request))

    def format_raw(self, result, request, indent=""):
        return ObjectFormatter.redirect_raw(result)

    def format_csv(self, result, request):
        """For now, format_csv is implemented in the same way as format_raw."""
        return ObjectFormatter.redirect_csv(result)

    def format_html(self, result, request):
        if request.code and request.code >= 300:
            title = "%d %s" % (request.code, request.code_message)
        else:
            title = request.path
        msg = ObjectFormatter.redirect_html(result)
        retval = """
        <html>
        <head><title>%s</title></head>
        <body>
        %s
        </body>
        </html>
        """ % (title, msg)
        return str(retval)


class ObjectFormatter(object):
    """This class and its subclasses are meant to do the real work of
        formatting individual objects.  The standard instance methods
        do the heavy lifting, which the static methods allow for
        delegation when needed.

        The instance methods (format_*) provide default implementations,
        but it is expected that they will be overridden to provide more
        useful information.
    """

    handlers = {}
    """ The handlers dictionary should have an entry for every subclass.
        Typically this will be defined immediately after defining the
        subclass.

    """

    def format_raw(self, result, indent=""):
        return indent + str(result)

    def format_csv(self, result):
        return self.format_raw(result)

    def format_html(self, result):
        return "<pre>%s</pre>" % result

    @staticmethod
    def redirect_raw(result, indent=""):
        handler = ObjectFormatter.handlers.get(result.__class__,
                ObjectFormatter.default_handler)
        return handler.format_raw(result, indent)

    @staticmethod
    def redirect_csv(result):
        handler = ObjectFormatter.handlers.get(result.__class__,
                ObjectFormatter.default_handler)
        return handler.format_csv(result)

    @staticmethod
    def redirect_html(result):
        handler = ObjectFormatter.handlers.get(result.__class__,
                ObjectFormatter.default_handler)
        return handler.format_html(result)

ObjectFormatter.default_handler = ObjectFormatter()


#if __name__=='__main__':
