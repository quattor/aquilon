# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014  Contributor
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


import httplib
import subprocess
import os

from aquilon.client.chunked import ChunkedHTTPConnection


class ProcessWrapper(object):

    class _closedsocket(object):
        def __getattr__(self, name):
            raise OSError(9, 'Bad file descriptor')

    def __init__(self, process):
        self.process = process
        self._stdout = process.stdout
        self._stdin = process.stdin

    def close(self):
        self._stdin.close()
        self._stdout.close()
        self._stdin = self.__class__._closedsocket()
        self._stdout = self.__class__._closedsocket()

    def makefile(self, mode, bufsize=None):
        return os.fdopen(os.dup(self._stdout.fileno()), mode, bufsize)

    def send(self, stuff, flags=0):
        if self.process.poll():
            raise httplib.NotConnected()

        return self._stdin.write(stuff)

    sendall = send

    def recv(self, len=1024, flags=0):
        if self.process.poll():
            raise httplib.NotConnected()

        return self._stdout.read(len)

    def __getattr__(self, attr):
        return getattr(self._stdout, attr)


class WrappedHTTPConnection(ChunkedHTTPConnection):

    def __init__(self, executable, host, port, service=None, strict=None):
        httplib.HTTPConnection.__init__(self, host, port, strict)
        self.executable = executable
        self.service = service

    def connect(self):
        try:
            # FIXME: The -o option requires knc >= 1.7.
            process = subprocess.Popen([self.executable,
                                        '-o', 'no-half-close',
                                        self.service + '@' + self.host,
                                        str(self.port)],
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        except OSError as e:
            raise httplib.NotConnected(e)

        self.sock = ProcessWrapper(process)
        self._process = process

    def getError(self):
        if not hasattr(self, '_process'):
            return 'no knc process'
        return self._process.stderr.read()


class KNCHTTPConnection(WrappedHTTPConnection):

    # Quick hack to support other environments...
    KNC_BIN = 'knc'
    KNC_PATH = '/ms/dist/kerberos/PROJ/knc/prod/bin'

    def __init__(self, host, port, service, strict=None):
        if os.path.exists(self.__class__.KNC_PATH):
            os.environ['PATH'] = "%s:%s" % (self.__class__.KNC_PATH,
                                            os.environ.get('PATH', ''))
        WrappedHTTPConnection.__init__(self, self.__class__.KNC_BIN,
                                       host, port, service, strict)
