from   pprint import pprint

class RefreshReport(object):
    def __init__(self, *args, **kw):
        self.adds = []
        self.dels = []
        self.upds = []
        self.errs = []

    def display(self):
        if self.adds:
            print 'Additions:'
            pprint(self.adds, indent=4)
        if self.dels:
            print 'Deletions:'
            pprint (self.dels, indent=4)
        if self.upds:
            print 'Updated:'
            pprint(self.upds, indent=4)
        if self.errs:
            print 'Errors:'
            pprint(self.errs, indent=4)

    def __repr__(self):
        msg = ''
        if self.adds:
            msg += 'Additions: %s\n\n'%(self.adds)
        if self.dels:
            msg += 'Deletions: %s\n\n'%(self.dels)
        if self.upds:
            msg += 'Updated: %s\n\n'%(self.upds)
        if self.errs:
            msg += 'Errors: %s\n\n'%(self.errs)
        return msg


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
