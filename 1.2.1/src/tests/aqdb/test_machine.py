#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon
""" tests create and delete of a machine through the session """
import sys
import os

import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..", "..")
    sys.path.insert(0, SRCDIR)

import aquilon.aqdb.depends
import aquilon.aqdb.db_factory         as aqdbf
import aquilon.aqdb.utils.shell        as shell
import aquilon.aqdb.hw.vendor          as v
import aquilon.aqdb.hw.model           as m
import aquilon.aqdb.hw.machine         as mc
import aquilon.aqdb.hw.cpu             as cpu
import aquilon.aqdb.loc.chassis        as ch

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

        self.chas = self.s.query(ch.Chassis).first()
        assert self.chas, "Can't find a chassis"

        self.nm = self.chas.name + 'n3'

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
                          location = self.chas, cpu = self.proc )

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
