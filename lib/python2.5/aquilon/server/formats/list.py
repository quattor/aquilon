#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""List formatter."""


from aquilon.server.formats.formatters import ObjectFormatter


class ListFormatter(ObjectFormatter):
    def format_raw(self, result, indent=""):
        return "\n".join([self.redirect_raw(item, indent) for item in result])

    def format_csv(self, result):
        return "\n".join([self.redirect_csv(item) for item in result])

    def format_html(self, result):
        return "<ul>\n<li>" + "<li>\n<li>".join(
                [self.redirect_html(item) for item in result]
                ) + "</li>\n</ul>\n"


ObjectFormatter.handlers[list] = ListFormatter()


#if __name__=='__main__':
