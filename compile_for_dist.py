#!/ms/dist/python/PROJ/core/2.5/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Add /ms/dist to traceback of files compiled in /ms/dev."""


import sys
import py_compile


def main(args=None):
    """Except for the custom dfile, this is stolen directly from py_compile.

    Compile all of the given filename arguments.  This custom version
    replaces /ms/dev in the path with /ms/dist to match our environment usage.

    """
    if args is None:
        args = sys.argv[1:]
    for filename in args:
        try:
            dfile = filename.replace('/ms/dev/', '/ms/dist/', 1)
            py_compile.compile(filename, dfile=dfile, doraise=True)
        except py_compile.PyCompileError, e:
            sys.stderr.write(e.msg)


if __name__ == "__main__":
    main()

