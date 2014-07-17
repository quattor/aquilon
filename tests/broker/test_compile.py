#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for testing the compile command."""

import os
import gzip
from cStringIO import StringIO
from cPickle import Pickler, Unpickler
from shutil import rmtree
from subprocess import Popen, PIPE
from datetime import datetime
import time

if __name__ == "__main__":
    import utils
    utils.import_depends()

import xml.etree.ElementTree as ET
import unittest2 as unittest
from brokertest import TestBrokerCommand
from notificationtest import VerifyNotificationsMixin


class TestCompile(VerifyNotificationsMixin, TestBrokerCommand):

    def get_profile_mtimes(self):
        """Returns a dictionary of objects to profile-info (indexed) mtimes.

        The dictionary key is the object name and does not include the
        suffix of the file.  Only objects that are listed with an
        expected suffix are included.

        """
        transparent_gzip = self.config.getboolean('panc', 'transparent_gzip')
        profilesdir = self.config.get('broker', 'profilesdir')
        index = os.path.join(profilesdir, 'profiles-info.xml')
        if self.gzip_profiles and transparent_gzip:
            source = gzip.open(index + '.gz')
        else:
            source = open(index)
        # TODO: hardcode XML profiles for now
        tree = ET.parse(source)
        mtimes = dict()
        for profile in tree.getiterator('profile'):
            if profile.text and "mtime" in profile.attrib:
                obj = profile.text.strip()
                for suffix in [self.xml_suffix, self.json_suffix]:
                    if obj and obj.endswith(suffix):
                        mtimes[obj[:-len(suffix)]] = \
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

        # Make sure some time is spent before we check if the mtime was updated
        last_update = max(stashed_mtimes.itervalues())
        if time.time() < last_update + 1:
            time.sleep(1)

    def test_100_addchange(self):
        # Touch the template used by utsi1 clients to trigger a recompile.
        template = self.template_name("service", "utsvc", "utsi1", "client",
                                      "config", domain="unittest")
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
        basetime = datetime.now()
        command = "compile --domain unittest"
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(err, "%s/%s compiled" % (total, total), command)
        # Index building is now asynchronous, so we have to wait for it
        self.wait_notification(basetime, 1)

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
        self.matchoutput(err, "No object profiles: nothing to do.", command)

    def test_410_manage(self):
        # using --force to bypass normal checks due to git status
        # containing uncommitted files
        command = ['manage', '--hostname=unittest02.one-nyp.ms.com',
                   '--sandbox=%s/out_of_date' % self.user, '--force']
        self.successtest(command)

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
        command = ['compile', '--hostname=unittest02.one-nyp.ms.com']
        self.successtest(command)
        self.statustest(["del_sandbox", "--sandbox", "out_of_date"])
        sandboxdir = os.path.join(self.sandboxdir, "out_of_date")
        rmtree(sandboxdir, ignore_errors=True)

    def test_500_adddebug(self):
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        template = self.find_template("aquilon", "archetype", "base",
                                      sandbox="utsandbox")
        with open(template) as f:
            contents = f.readlines()
        # These templates can't just have random debug statements...
        # hiding it inside a variable statement works, though.
        contents.append("variable AQDDEBUGBASE = "
                        "debug('aqd unittest debug for aquilon base');\n")
        with open(template, 'w') as f:
            f.writelines(contents)
        template = self.find_template("aquilon", "archetype", "final",
                                      sandbox="utsandbox")
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

    def test_550_compilepersonality(self):
        command = "compile --personality compileserver --archetype aquilon"
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(err, "0/10 object template(s) being processed",
                         command)

    def test_560_compilepersonality(self):
        command = ['manage', '--hostname=unittest02.one-nyp.ms.com',
                   '--domain=ut-prod', '--force']
        self.successtest(command)
        command = ['compile', '--personality=compileserver', '--archetype=aquilon']
        err = self.badrequesttest(command)
        self.matchoutput(err, 'Bad Request: All hosts must be in the same domain or sandbox:',
                         command)
        self.matchoutput(err, '1 hosts in domain ut-prod', command)

    def test_570_compilepersonalityidomain(self):
        command = ['compile', '--personality=compileserver', '--archetype=aquilon',
                   '--domain=ut-prod']
        (out, err) = self.successtest(command)
        self.matchoutput(err, "1/1 object template(s) being processed",
                         command)

    def test_575_compilepersonalitynohost(self):
        command = ['compile', '--personality=utpersonality/dev', '--archetype=aquilon',
                   '--domain=ut-prod']
        (out, err) = self.successtest(command)
        self.noouttest(command)

    def test_580_reset_data(self):
        command = ['manage', '--hostname=unittest02.one-nyp.ms.com',
                   '--domain=unittest', '--force']
        self.successtest(command)
        # Make sure the build files exist - further tests depend on that
        command = ['compile', '--hostname=unittest02.one-nyp.ms.com']
        self.successtest(command)

    def test_600_aqcompile(self):
        aqcompile = os.path.join(self.config.get("broker", "srcdir"),
                                 "bin", "aq_compile.py")
        basedir = self.config.get("broker", "quattordir")
        templates = os.path.join(self.sandboxdir, "utsandbox")
        swrep = self.config.get("broker", "swrepdir")
        args = [aqcompile, "--basedir", basedir, "--domain", "utsandbox",
                "--templates", templates, "--swrep", swrep,
                "--batch_size", "10"]
        if self.config.getboolean('panc', 'gzip_output'):
            args.append("--compress_output")
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        self.assertEqual(p.returncode, 0,
                         "Non-0 return code %s for %s, "
                         "STDOUT:\n@@@\n'%s'\n@@@\n"
                         "STDERR:\n@@@\n'%s'\n@@@\n"
                         % (p.returncode, args, out, err))
        self.matchoutput(out, "BUILD SUCCESSFUL", args)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCompile)
    unittest.TextTestRunner(verbosity=2).run(suite)
