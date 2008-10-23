#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Restore a snapshot of the base directory and database."""

# Parse options for the snapshot stamp
# verify the directory exists
# If there is a current basedir:
#   Snapshot it (if not --nuke)
#   Remove it
# Clear the database
# cp -a
# Read the database password
# Do an import from the aqdb directory

