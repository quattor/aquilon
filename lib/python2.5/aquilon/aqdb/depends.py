import os
import ms.version

#####
# NEVER check in a version of this file to a for_next branch with 'dev'
# in an addpkg call!!!
#####

#if os.getlogin() == 'daqscott' and os.path.isdir(_DEV):
#    ms.version.addpkg('sqlalchemy', '0.5beta', 'dev')
#else:
ms.version.addpkg('sqlalchemy','0.4.8')

ms.version.addpkg('cx_Oracle','4.4-10.2.0.1')

ms.version.addpkg('ibm_db','0.2.9-9.5.1')

ms.version.addpkg('ipython','0.9.1')

ms.version.addpkg('nose','0.10.3')

#ms.version.addpkg('sqlalchemy-migrate', '0.4.5', 'dev')

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon
