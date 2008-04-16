#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent- tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''If you can read this, you should be Documenting'''
'''The Twisted modules used by the server really do not get along
well with ipython.  If we are in the server, wrap the call so that
it does not get brought in.'''

import sys
import os
user = os.environ.get('USER')

def dummy_ipshell(msg):
    print >>sys.stderr, msg

if sys.modules.has_key('twisted.scripts.twistd'):
    ipshell = dummy_ipshell("In the server, not actually calling ipshell()!")

elif user == 'quattor' or user == 'cdb':
    """ ipython likes to create rc files for you, but prod ids have read only
        home dirs, and spewage ensues """
    ipshell = dummy_ipshell("quattor prodid can't use ipython...")

else:
    import msversion
    msversion.addpkg('ipython','0.7.2','dist')

    from IPython.Shell import IPShellEmbed
    ipshell = IPShellEmbed()

#TODO: write this for oracle instance...
#for now, run sqlplus @utils/drop.sql, over and over until nothing is left
#def tear_down_instance():
#    meta.drop_all()

if __name__ == '__main__':
    sys.path.append('../..')

    from db import meta, Session

    from location import *
    from network import *
    from service import *
    from configuration import *
    from hardware import *
    from interface import *
    from auth import *
    #from population_scripts import least_loaded
    s=Session()

    ipshell()
