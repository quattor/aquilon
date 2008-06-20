#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" subtypes of machines """
import sys
sys.path.insert(0, '..')
sys.path.insert(1,'../..')
sys.path.insert(2,'../../..')

from subtypes import subtype

MachineType = subtype('MachineType','machine_type')
machine_type = MachineType.__table__

def populate_machine_type():
    if empty(machine_type):
        print "Populating machine_type"
        fill_type_table(machine_type,
                        ['rackmount', 'blade', 'workstation',])
