#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2012  Contributor
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

import sys, os
# bin/twistd.py, we'll start it after the patch is done
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "..", "..", "..", "bin"))
# lib/python2.6/config.py
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "..", "..", "..", "lib", "python2.6"))

from aquilon.config import Config
from socket import gaierror
import socket
import re

# dwim options parser
for i in range(0,len(sys.argv)):
    if sys.argv[i] == "--config":
        configpath = sys.argv[i + 1]
        break

config = Config(configfile=configpath)


# do the patches


def fake_gethostbyname(hostname):
    try:
        host_ip = None

        # for templates/index.py
        if hostname == config.get("broker", "bind_address"):
            host_ip = gethostbyname_orig(hostname)
        else:
            # faking hostip
            fake_hosts = config.get('unittest', 'fake_hosts_location')
            hostfilename = fake_hosts + hostname

            # strip domain part
            if not os.path.exists(hostfilename) and hostname.find(".") > -1:
                hostfilename = fake_hosts + hostname[:hostname.find(".")]

            hostfile = open(hostfilename).readlines()
            primary_name = hostfile[0].split()[2]
            ip_re = re.compile(r'^\s*([a-z0-9]+)\s+[a-z0-9]+\s+([0-9\.]+)')
            for line in hostfile:
                m = ip_re.search(line)
                if m and primary_name == m.group(1):
                    host_ip = m.group(2)
                    break

        if host_ip == None:
            raise gaierror(-2, "Name or service not known")

        return host_ip

    except IOError, e:
        # To have the cause in aqd.log
        raise gaierror(-2, "Name or service not known %s" % e)

gethostbyname_orig = socket.gethostbyname
socket.gethostbyname = fake_gethostbyname

# worker/resources.py depends on it.
sys.argv[0] = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "..", "..", "..", "bin", "twistd.py")

# start the broker
import twistd