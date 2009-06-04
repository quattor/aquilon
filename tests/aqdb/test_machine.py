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
""" tests create and delete of a machine through the session """
import sys
import os

import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..", "lib", "python2.5")
    sys.path.insert(0, SRCDIR)

import aquilon.aqdb.depends
import aquilon.aqdb.db_factory         as aqdbf
import aquilon.aqdb.utils.shutils      as shell
import aquilon.aqdb.hw.vendor          as v
import aquilon.aqdb.hw.model           as m
import aquilon.aqdb.hw.machine         as mc
import aquilon.aqdb.hw.cpu             as cpu
import aquilon.aqdb.loc.rack           as rk

class testMachine(unittest.TestCase):
    def setUp(self, vendor='hp', model='bl45p', *args, **kw):

        self.dbf = aqdbf.db_factory()
        self.s   = self.dbf.Session()

        self.vnd = self.s.query(v.Vendor).filter_by(name=vendor).one()
        assert self.vnd, "Can't find vendor %s"%(vendor)

        self.mdl  = self.s.query(m.Model).filter_by(name=model).one()
        assert self.mdl, "Can't find model %s"%(model)

        self.proc = self.s.query(cpu.Cpu).first()
        assert self.proc, "Can't find a cpu"

        self.rack = self.s.query(rk.Rack).first()
        assert self.rack, "Can't find a rack"

        self.nm = self.rack.name + 'c1n3'

        t = self.s.query(mc.Machine).filter_by(name = self.nm).first()
        if t is not None:
            self.s.delete(t)
            self.s.commit()

    def tearDown(self):
        #TODO: this is a recursive definition. Fix it with a direct sql statement later on
        if len(self.s.query(mc.Machine).filter_by(name = self.nm).all()) > 0:
            self.testDelMachine()

    def testInitMachine(self, *args, **kw):

        mchn = mc.Machine(name = self.nm, model = self.mdl,
                          location = self.rack, cpu = self.proc )

        try:
            self.s.save(mchn)
        except Exception, e:
            print e
            sys.exit(2)

        self.s.commit()

        assert mchn, 'Commit machine failed'

    def testDelMachine(self):
        mchn = self.s.query(mc.Machine).filter_by(name = self.nm).one()

        self.s.delete(mchn)
        self.s.commit()

        t = self.s.query(mc.Machine).filter_by(name = self.nm).first()
        assert t is None

    def runTest(self):
        self.setUp()
        self.testInitMachine()
        self.testDelMachine()
        self.tearDown()

if __name__ == "__main__":
    tm = testMachine()
    tm.runTest()
