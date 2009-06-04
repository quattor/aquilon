#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Scale test for parallel execution."""


import os
import time
from subprocess import Popen
from datetime import datetime
from random import choice
from optparse import OptionParser


parser = OptionParser()
parser.add_option("-q", "--queuesize", dest="queuesize", type="int", default=4,
                  help="Length of the parallel queue.")
parser.add_option("-t", "--target", dest="target", type="int", default=4,
                  help="Stop adding work when this many updates scheduled.")
parser.add_option("-a", "--aqservice", dest="aqservice", type="string",
                  help="The service name to use when connecting to aqd")
(options, args) = parser.parse_args()

DIR=os.path.realpath(os.path.dirname(__file__))
# Dictionary of rack -> subnet
allocated = {}
free_racks = range(8)
free_subnets = range(8)
building = "np"
queue = []

results = {"add":[], "update":[], "show":[], "delete":[]}


class WorkUnit(object):
    def __init__(self, action):
        self.action = action
        self.building = "np"
        self.update_globals_start()
        self.start()

    def update_globals_start(self):
        if self.action == "add":
            self.rackid = free_racks.pop()
            self.subnet = free_subnets.pop()
        elif self.action == "update":
            (self.rackid, self.oldsubnet) = allocated.popitem()
            self.subnet = free_subnets.pop()
        elif self.action == "delete":
            (self.rackid, self.subnet) = allocated.popitem()

    def start(self):
        self.start = datetime.now()
        if self.action == "add":
            cmd = [os.path.join(DIR, "add_rack.py"),
                   "--building", self.building, "--rack", str(self.rackid),
                   "--subnet", str(self.subnet)]
        elif self.action == "update":
            cmd = [os.path.join(DIR, "update_rack.py"),
                   "--building", self.building, "--rack", str(self.rackid),
                   "--subnet", str(self.subnet)]
        elif self.action == "show":
            cmd = [os.path.join(DIR, "show_info.py")]
        elif self.action == "delete":
            cmd = [os.path.join(DIR, "del_rack.py"),
                   "--building", self.building, "--rack", str(self.rackid)]
        if options.aqservice:
            cmd.append("--aqservice")
            cmd.append(options.aqservice)
        self.process = Popen(cmd, stdout=1, stderr=2)
        return

    def update_globals_end(self):
        if self.action == "add":
            allocated[self.rackid] = self.subnet
        elif self.action == "update":
            free_subnets.append(self.oldsubnet)
            allocated[self.rackid] = self.subnet
        elif self.action == "delete":
            free_racks.append(self.rackid)
            free_subnets.append(self.subnet)

    def poll(self):
        rc = self.process.poll()
        if rc is not None:
            self.end = datetime.now()
            results[self.action].append(self.end - self.start)
            self.update_globals_end()
        return rc

    @classmethod
    def create(cls):
        actions = ["add", "update", "delete", "show"]
        if not free_racks or not free_subnets:
            actions.remove("add")
        if not free_subnets or not allocated:
            actions.remove("update")
        if not allocated:
            actions.remove("delete")
        return WorkUnit(choice(actions))


while True:
    for workunit in queue:
        if workunit.poll() is not None:
            queue.remove(workunit)
    if len(results["update"]) >= options.target:
        break
    while len(queue) < options.queuesize:
        queue.append(WorkUnit.create())
    # log current queue?
    time.sleep(1)

# Drain the queue, free everything...
while queue or allocated:
    for workunit in queue:
        if workunit.poll() is not None:
            queue.remove(workunit)
    while allocated and len(queue) < options.queuesize:
        queue.append(WorkUnit("delete"))
    time.sleep(1)

for key, values in results.items():
    if values:
        print
        print "%s:" % key
        print str(values)
        values.sort()
        min = values[0]
        print
        print "  min: %d.%d seconds" % (min.seconds, min.microseconds)
        max = values[-1]
        print "  max: %d.%d seconds" % (max.seconds, max.microseconds)
        print


#if __name__=='__main__':
