# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
"""Contains the logic for `aq show active`."""


import os
import re

from aquilon.server.broker import BrokerCommand
from aquilon.server.processes import read_file


class CommandShowActive(BrokerCommand):

    requires_transaction = False
    requires_azcheck = False

    def render(self, **arguments):
        logdir = self.config.get("broker", "logdir")
        commands = {}
        logs = {}
        for f in ["aqd.log.1", "aqd.log"]:
            logfile = os.path.join(logdir, f)
            if os.path.exists(logfile):
                self.read_logfile(logfile, commands, logs)
        retval = []
        for id in [str(i) for i in sorted([int(s) for s in commands.keys()])]:
            command = commands[id]
            retval.append("[%(id)s] %(user)s: aq %(command)s%(args)s" %
                          command)
            if logs.get(command['channel'], None):
                for line in logs[command['channel']]:
                    retval.append("(%s) %s" % (id, line))
        return "\n".join(retval)

    starting_re = re.compile(r'^(?P<timestamp>[\s\d:+-]+) \[-\] Starting aqd')
    incoming_re = re.compile(r'^(?P<timestamp>[\s\d:+-]+) \[(?P<channel>.*?)\]'
                             r' Incoming command #(?P<id>\d+)'
                             r' from user=(?P<user>\S+)'
                             r' aq (?P<command>\S+)'
                             r' with arguments {(?P<bareargs>.*)}')
    finished_re = re.compile(r'^(?P<timestamp>[\s\d:+-]+) \[-\]'
                             r' Command #(?P<id>\d+) finished.')
    log_re = re.compile(r'^(?P<timestamp>[\s\d:+-]+) \[(?P<channel>.*?)\]'
                        r' (?P<log>.*)$')
    args_re = re.compile(r'\'(?P<option>\w+)\': (?P<parameter>\'.*?\')')

    def read_logfile(self, logfile, commands, logs):
        f = open(logfile)
        try:
            for line in f:
                line = line.rstrip()
                m = self.starting_re.match(line)
                if m:
                    self.clear_all(commands, logs)
                    continue
                m = self.incoming_re.match(line)
                if m:
                    command = self.massage_matched_command(m.groupdict())
                    commands[command['id']] = command
                    continue
                m = self.finished_re.match(line)
                if m:
                    self.clear_command(commands, logs, m.groupdict()['id'])
                    continue
                m = self.log_re.match(line)
                if m:
                    loginfo = m.groupdict()
                    if loginfo['channel'] == '-':
                        continue
                    self.save_log(commands, logs, loginfo)
                    continue
        finally:
            f.close()

    def clear_all(self, commands, logs):
        commands.clear()
        logs.clear()

    def massage_matched_command(self, command):
        command = command.copy()
        args = []
        for a in self.args_re.finditer(command['bareargs']):
            if a.groupdict()['option'] == 'format' and \
               a.groupdict()['parameter'] == "'raw'":
                continue
            if a.groupdict()['parameter'] == "'True'":
                args.append(" --%(option)s" % a.groupdict())
            else:
                args.append(" --%(option)s=%(parameter)s" % a.groupdict())
        command['args'] = "".join(args)
        return command

    def clear_command(self, commands, logs, id):
        command = commands.pop(id, None)
        if command:
            logs.pop(command['channel'], None)

    def save_log(self, commands, logs, loginfo):
        if logs.get(loginfo['channel'], None):
            logs[loginfo['channel']].append(loginfo['log'])
        else:
            logs[loginfo['channel']] = [loginfo['log']]


