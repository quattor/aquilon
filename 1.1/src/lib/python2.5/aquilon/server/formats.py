#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Container for the Formatter class.  For now, holds all utility
methods, but they will probably be split out into separate files.

"""

class Formatter(object):
    def __init__(self, *args, **kwargs):
        object.__init__(self, *args, **kwargs)
        self.formats = []
        for attr in dir(self):
            if not attr.startswith("format_"):
                continue
            if not callable(getattr(self,attr)):
                continue
            self.formats.append(attr[7:])

    def format(self, style, result, request):
        if not style:
            style = "raw"
        formatter = getattr(self, "format_" + style, self.format_raw)
        return formatter(result, request)

    def format_raw(self, result, request):
        # Any sort of custom printing here might be better suited for
        # a different formatting function.
        if isinstance(result, list):
            return "\n".join([str(item) for item in result])
        return str(result)

    # FIXME: This should eventually be some sort of dynamic system...
    # maybe try to ask result how it should be rendered, or check the
    # request for hints.  For now, just wrap in a basic document.
    def format_html(self, result, request):
        if request.code and request.code >= 300:
            title = "%d %s" % (request.code, request.code_message)
        else:
            title = request.path
        if isinstance(result, list):
            msg = "<ul>\n<li>" + "</li>\n<li>".join(
                    [str(item) for item in result]) + "</li>\n</ul>\n"
        else:
            msg = str(result)
        retval = """
        <html>
        <head><title>%s</title></head>
        <body>
        %s
        </body>
        </html>
        """ % (title, msg)
        return str(retval)


#if __name__=='__main__':
