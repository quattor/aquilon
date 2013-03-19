#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the compile command."""

import os
import unittest
import gzip
from cStringIO import StringIO
from cPickle import Pickler, Unpickler

import xml.etree.ElementTree as ET

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestCompile(TestBrokerCommand):

    def get_profile_mtimes(self):
        """Returns a dictionary of objects to profile-info (indexed) mtimes.

        The dictionary key is the object name and does not include the
        suffix of the file.  Only objects that are listed with an
        expected suffix are included.

        """
        advertise_xml = self.config.getboolean('panc', 'advertise_gzip_as_xml')
        profilesdir = self.config.get('broker', 'profilesdir')
        index = os.path.join(profilesdir, 'profiles-info.xml')
        if self.gzip_profiles and advertise_xml:
            source = gzip.open(index + '.gz')
            profile_suffix = '.xml'
        else:
            source = open(index)
            profile_suffix = self.profile_suffix
        tree = ET.parse(source)
        mtimes = dict()
        for profile in tree.getiterator('profile'):
            if profile.text and "mtime" in profile.attrib:
                obj = profile.text.strip()
                if obj and obj.endswith(profile_suffix):
                    mtimes[obj[:-len(profile_suffix)]] = \
                            int(profile.attrib['mtime'])
        return mtimes

    def test_000_precompile(self):
        # Before the tests below, make sure everything is up to date.
        command = "compile --domain unittest"
        (out, err) = self.successtest(command.split(" "))

    def test_010_index(self):
        # Verify and stash mtimes
        stashed_mtimes = self.get_profile_mtimes()
        buffer = StringIO()
        pickler = Pickler(buffer)
        pickler.dump(stashed_mtimes)
        scratchfile = self.writescratch("stashed_mtimes", buffer.getvalue())

        command = ["search_host", "--domain=unittest",
                   "--service=utsvc", "--instance=utsi1"]
        hosts = self.commandtest(command).splitlines()
        # Failure here could mean:
        # - The host profile is not in the index
        # - The host profile is in the index but with the wrong extension.
        for host in hosts:
            self.assertTrue(host in stashed_mtimes,
                            "host %s missing from profiles-info" % host)

    def test_100_addchange(self):
        # Touch the template used by utsi1 clients to trigger a recompile.
        domaindir = os.path.join(self.config.get("broker", "domainsdir"),
                                 "unittest")
        template = os.path.join(domaindir, "service", "utsvc", "utsi1",
                                "client", "config.tpl")
        f = open(template)
        try:
            contents = f.readlines()
        finally:
            f.close()
        contents.append("#Added by unittest broker/test_compile\n")
        f = open(template, 'w')
        try:
            f.writelines(contents)
        finally:
            f.close()

    def test_200_compileunittest(self):
        hosts = self.commandtest(["search_host", "--domain=unittest",
                                  "--service=utsvc", "--instance=utsi1"]
                                ).splitlines()
        total = len(hosts)
        command = "compile --domain unittest"
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(err, "%s/%s compiled" % (total, total), command)

    def test_210_index(self):
        new_mtimes = self.get_profile_mtimes()
        buffer = StringIO(self.readscratch("stashed_mtimes"))
        unpickler = Unpickler(buffer)
        stashed_mtimes = unpickler.load()

        command = ["search_host", "--domain=unittest", "--service=utsvc",
                   "--instance=utsi1"]
        hosts = self.commandtest(command).splitlines()
        for host in hosts:
            self.assertTrue(host in stashed_mtimes,
                            "host %s missing from old profiles-info" % host)
            self.assertTrue(host in new_mtimes,
                            "host %s missing from new profiles-info" % host)
            self.assertTrue(new_mtimes[host] > stashed_mtimes[host],
                            "host %s mtime %s not greater than original %s" %
                            (host, new_mtimes[host], stashed_mtimes[host]))

    def test_300_compilehost(self):
        command = "compile --hostname unittest02.one-nyp.ms.com"
        (out, err) = self.successtest(command.split(" "))
        # This should have been compiled above...
        self.matchoutput(err, "0/1 object template(s) being processed",
                         command)

    def test_400_addsandbox(self):
        command = "add_sandbox --sandbox=out_of_date --start=utsandbox"
        self.successtest(command.split())

    def test_405_compileempty(self):
        command = "compile --sandbox %s/out_of_date" % self.user
        (out, err) = self.successtest(command.split(' '))
        # Funny enough, this message doesn't actually get returned
        # to the client.
        #self.matchoutput(out, "no hosts: nothing to do", command)
        self.assertEmptyOut(out, command)
        self.matchoutput(err,
                         "Sandbox %s/out_of_date does not contain the "
                         "latest changes from the prod domain.  If "
                         "there are failures try "
                         "`git fetch && git merge origin/prod`" % self.user,
                         command)

    def test_410_manage(self):
        # using --force to bypass normal checks due to git status
        # containing uncommitted files
        command = ['manage', '--hostname=unittest02.one-nyp.ms.com',
                   '--sandbox=%s/out_of_date' % self.user, '--force']
        self.successtest(command)

    def test_415_compilebehind(self):
        command = ['compile', '--sandbox=%s/out_of_date' % self.user]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "Sandbox %s/out_of_date does not contain the "
                         "latest changes from the prod domain.  If "
                         "there are failures try "
                         "`git fetch && git merge origin/prod`" % self.user,
                         command)

    def test_420_update(self):
        sandboxdir = os.path.join(self.sandboxdir, 'out_of_date')
        self.gitcommand(['fetch'], cwd=sandboxdir)
        self.gitcommand(['merge', 'origin/prod'], cwd=sandboxdir)

    def test_425_compileupdated(self):
        command = ['compile', '--sandbox=%s/out_of_date' % self.user]
        (out, err) = self.successtest(command)
        self.matchclean(err,
                         "Sandbox %s/out_of_date does not contain the "
                         "latest changes from the prod domain." % self.user,
                         command)

    def test_430_cleanup(self):
        # using --force to bypass normal checks due to git status
        # containing uncommitted files
        command = ['manage', '--hostname=unittest02.one-nyp.ms.com',
                   '--domain=unittest', '--force']
        self.successtest(command)
        command = ['manage', '--hostname=unittest02.one-nyp.ms.com',
                   '--domain=unittest', '--force']
        self.successtest(command)
        command = ['compile', '--hostname=unittest02.one-nyp.ms.com']
        self.successtest(command)

    def test_500_adddebug(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        template = os.path.join(sandboxdir, "aquilon", "archetype", "base.tpl")
        with open(template) as f:
            contents = f.readlines()
        # These templates can't just have random debug statements...
        # hiding it inside a variable statement works, though.
        contents.append("variable AQDDEBUGBASE = "
                        "debug('aqd unittest debug for aquilon base');\n")
        with open(template, 'w') as f:
            f.writelines(contents)
        template = os.path.join(sandboxdir, "aquilon", "archetype", "final.tpl")
        with open(template) as f:
            contents = f.readlines()
        contents.append("variable AQDDEBUGFINAL = "
                        "debug('aqd unittest debug for aquilon final');\n")
        with open(template, 'w') as f:
            f.writelines(contents)
        self.gitcommand(["commit", "-a",
                         "-m", "added unittest debug statements"],
                        cwd=sandboxdir)
        self.successtest(["publish", "--branch", "utsandbox"],
                         env=self.gitenv(), cwd=sandboxdir)

    def test_505_verifynodebug(self):
        command = ['compile', '--domain=unittest', '--cleandeps']
        (out, err) = self.successtest(command)
        self.matchoutput(err, "0 errors", command)
        self.matchclean(err, "aqd unittest debug for aquilon base", command)
        self.matchclean(err, "aqd unittest debug for aquilon final", command)

    # The 'Assigning repositories to packages...' line is a debug() in
    # aquilon/components/spma/functions.tpl that is used here to verify
    # that the auto-exclude from pancdebug is working.
    def test_510_verifydebughost(self):
        command = ['compile', '--hostname=unittest02.one-nyp.ms.com',
                   '--pancdebug', '--cleandeps']
        (out, err) = self.successtest(command)
        self.matchoutput(err, "aqd unittest debug for aquilon base", command)
        self.matchoutput(err, "aqd unittest debug for aquilon final", command)
        self.matchclean(err, "Assigning repositories to packages...", command)

    def test_520_verifydebugdomain(self):
        command = ['compile', '--domain=unittest', '--pancdebug',
                   '--cleandeps']
        (out, err) = self.successtest(command)
        self.matchoutput(err, "aqd unittest debug for aquilon base", command)
        self.matchoutput(err, "aqd unittest debug for aquilon final", command)
        self.matchclean(err, "Assigning repositories to packages...", command)

    # If this fails on the 'Assigning...' line then all four tests
    # (510, 520, 530, 540) should be revisited.  See comments above 510.
    def test_530_verifyexclude(self):
        command = ['compile', '--hostname=unittest02.one-nyp.ms.com',
                   '--pancexclude=archetype/base',
                   '--pancinclude=.*', '--cleandeps']
        (out, err) = self.successtest(command)
        self.matchclean(err, "aqd unittest debug for aquilon base", command)
        self.matchoutput(err, "aqd unittest debug for aquilon final", command)
        self.matchoutput(err, "Assigning repositories to packages...", command)

    def test_540_verifyinclude(self):
        command = ['compile', '--hostname=unittest02.one-nyp.ms.com',
                   '--pancinclude=archetype/base', '--cleandeps']
        (out, err) = self.successtest(command)
        self.matchoutput(err, "aqd unittest debug for aquilon base", command)
        self.matchclean(err, "aqd unittest debug for aquilon final", command)
        self.matchclean(err, "Assigning repositories to packages...", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCompile)
    unittest.TextTestRunner(verbosity=2).run(suite)
