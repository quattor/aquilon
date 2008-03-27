#!/ms/dist/python/PROJ/core/2.5.0/bin/python -W ignore
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''If you can read this, you should be Documenting'''

from sys import path
#path.append('./utils')
path.append('../..')

from aquilon.aqdb.utils.debug import ipshell
from DB import meta, engine, Session

s = Session()

from location import *
from network import *
from service import *
#from configuration import *

s=Session()


ipshell()
