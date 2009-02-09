import os
import sys

_DIR = os.path.dirname(os.path.realpath(__file__))
_LIBDIR = os.path.join(_DIR, "..", "..", "lib", "python2.5")

if _LIBDIR not in sys.path:
    sys.path.insert(0,_LIBDIR)

import aquilon.aqdb.depends
