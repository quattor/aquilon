#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Basic module for running tests on broker commands."""

import os
import sys
import unittest
from subprocess import Popen, PIPE

from aquilon.config import Config

class TestBrokerCommand(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def commandtest(self, command):
        config = Config()
        aq = os.path.join(config.get("broker", "srcdir"), "bin", "aq")
        kncport = config.get("broker", "kncport")
        if isinstance(command, list):
            args = command[:]
        else:
            args = [command]
        args.insert(0, aq)
        args.insert(1, "--aqport")
        args.insert(2, kncport)
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        (out, err) = p.communicate()
        self.assertEqual(err, "",
                "STDERR for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, err))
        self.assertEqual(p.returncode, 0,
                "Non-zero return code for %s, STDOUT:\n@@@\n'%s'\n@@@\n"
                % (command, out))
        return out

    def noouttest(self, command):
        out = self.commandtest(command)
        self.assertEqual(out, "",
                "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, out))


#if __name__=='__main__':

