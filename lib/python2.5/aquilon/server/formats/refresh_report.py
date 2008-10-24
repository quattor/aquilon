#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Formatter for 'refresh' (as in network refresh) reports."""


from StringIO import StringIO
from pprint import PrettyPrinter

from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.data_sync.refresh_report import RefreshReport


class RefreshReportFormatter(ObjectFormatter):
    def format_raw(self, rr, indent=""):
        s = StringIO()
        pp = PrettyPrinter(stream=s, indent=4)
        if rr.adds:
            print >>s, 'Additions:'
            pp.pprint(rr.adds)
        if rr.dels:
            print >>s, 'Deletions:'
            pp.pprint(rr.dels)
        if rr.upds:
            print >>s, 'Updated:'
            pp.pprint(rr.upds)
        if rr.errs:
            print >>s, 'Errors:'
            pp.pprint(rr.errs)
        return s.getvalue()

ObjectFormatter.handlers[RefreshReport] = RefreshReportFormatter()


#if __name__=='__main__':
