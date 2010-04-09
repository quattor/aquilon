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
"""Test module for starting the broker."""

import os
import sys
import unittest
from subprocess import Popen, PIPE

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(__file__))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from aquilon.config import Config


class TestBrokerStart(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def teststart(self):
        # FIXME: Either remove any old pidfiles, or ignore it as a warning
        # from stderr... or IMHO (daqscott) if pid files exist and are knc or
        # python processes, kill -9 the pids and delete the files (with a
        # warning message it tickles you)

        config = Config()
        twistd = os.path.join(config.get("broker", "srcdir"),
                              "bin", "twistd.py")
        pidfile = os.path.join(config.get("broker", "rundir"), "aqd.pid")
        logfile = config.get("broker", "logfile")

        # Specify twistd and options...
        args = [sys.executable, twistd,
                "--pidfile", pidfile, "--logfile", logfile]

        if config.has_option("unittest", "profile"):
            if config.getboolean("unittest", "profile"):
                args.append("--profile")
                args.append(os.path.join(config.get("broker", "logdir"),
                                         "aqd.profile"))
                args.append("--profiler=cProfile")
                args.append("--savestats")

        # And then aqd and options...
        args.extend(["aqd", "--config", config.baseconfig])

        if config.has_option("unittest", "coverage"):
            if config.getboolean("unittest", "coverage"):
                args.append("--coverage")
                args.append(os.path.join(config.get("broker", "logdir"),
                                         "aqd.coverage"))

        p = Popen(args)
        self.assertEqual(p.wait(), 0)

        # FIXME: Check that it is listening on the correct port(s)...

        # FIXME: If it fails, either cat the log file, or tell the user to try
        # running '%s -bn aqd --config %s'%(twistd, config.baseconfig)

    def testrsynctemplateking(self):
        config = Config()
        # Duplicated from runtests.py
        p = Popen(("rsync", "-avP", "-e", "ssh", "--delete",
                   "--exclude=.git/config",
                   os.path.join(config.get("unittest", "template_king_path"),
                                ""),
                   config.get("broker", "kingdir")),
                  stdout=PIPE, stderr=PIPE)
        (out, err) = p.communicate()
        # Ignore out/err unless we get a non-zero return code, then log it.
        self.assertEqual(p.returncode, 0,
                         "Non-zero return code for rsync of template-king, "
                         "STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                         % (out, err))
        p = Popen(("rsync", "-avP", "-e", "ssh",
                   config.get("unittest", "template_king_config"),
                   os.path.join(config.get("broker", "kingdir"), ".git")),
                  stdout=1, stderr=2)
        (out, err) = p.communicate()
        # Ignore out/err unless we get a non-zero return code, then log it.
        self.assertEqual(p.returncode, 0,
                         "Non-zero return code for rsync of template-king, "
                         "STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                         % (out, err))
        return


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBrokerStart)
    unittest.TextTestRunner(verbosity=2).run(suite)

