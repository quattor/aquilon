#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Test module for starting the broker."""

import os
import sys
import unittest
from subprocess import Popen, PIPE

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from aquilon.config import Config


class TestBrokerStart(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def teststart(self):
        # FIXME: Either remove any old pidfiles, or ignore it as a warning
        # from stderr...
        config = Config()
        twistd = os.path.join(config.get("broker", "srcdir"), "bin", "twistd")
        pidfile = os.path.join(config.get("broker", "rundir"), "aqd.pid")
        logfile = config.get("broker", "logfile")
        args = [twistd, "--pidfile", pidfile, "--logfile", logfile,
                "aqd", "--config", config.baseconfig]
        p = Popen(args)
        #p = Popen(args, stdout=PIPE, stderr=PIPE)
        #(out, err) = p.communicate()
        #self.assertEqual(err, "")
        #self.assertEqual(out, "")
        self.assertEqual(p.wait(), 0)
        # FIXME: Check that it is listening on the correct port(s)...

    def testrsynctemplateking(self):
        config = Config()
        template_king_host = config.get("unittest", "template_king_host")
        p = Popen(("rsync", "-avP", "-e", "ssh", "--delete",
            "%s:/var/quattor/template-king" % template_king_host,
            # Minor hack... ignores config kingdir...
            config.get("broker", "quattordir")),
            stdout=PIPE, stderr=PIPE)
        (out, err) = p.communicate()
        # Ignore out/err unless we get a non-zero return code, then log it.
        self.assertEqual(p.returncode, 0,
                "Non-zero return code for rsync of template-king, STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                % (out, err))
        return


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBrokerStart)
    unittest.TextTestRunner(verbosity=2).run(suite)

