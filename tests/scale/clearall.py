#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Clean up any entries."""


import os
from subprocess import Popen


DIR=os.path.realpath(os.path.dirname(__file__))
free_racks = range(8)
free_subnets = range(8)
building = "np"

processes = []
for rackid in free_racks:
    processes.append(Popen([os.path.join(DIR, "del_rack.py"),
        "--building", building, "--rack", str(rackid)], stdout=1, stderr=2))

for process in processes:
    process.wait()


#if __name__=='__main__':
