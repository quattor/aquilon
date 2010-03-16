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


import httplib
import subprocess
import os

from aquilon.client.chunked import ChunkedHTTPConnection


class ProcessWrapper(object):

    class _closedsocket:
        def __getattr__(self, name):
            raise error(9, 'Bad file descriptor')

    def __init__(self, process):
        self.process = process
        self._stdout = process.stdout
        self._stdin = process.stdin

    def close(self):
        self._stdin.close()
        self._stdout.close()
        self._stdin = self.__class__._closedsocket()
        self._stdout = self.__class__._closedsocket()

    def makefile(self, mode, bufsize = None):
        return os.fdopen(os.dup(self._stdout.fileno()), mode, bufsize)

    def send(self, stuff, flags = 0):
        if self.process.poll():
            raise httplib.NotConnected()

        return self._stdin.write(stuff)

    sendall = send

    def recv(self, len = 1024, flags = 0):
        if self.process.poll():
            raise httplib.NotConnected()

        return self._stdout.read(len)

    def __getattr__(self, attr):
        return getattr(self._stdout, attr)


class WrappedHTTPConnection(ChunkedHTTPConnection):

    def __init__(self, executable, host, port, service = None, strict = None):
        httplib.HTTPConnection.__init__(self, host, port, strict)
        self.executable = executable
        self.service = service

    def connect(self):
        try:
            process = subprocess.Popen([self.executable, self.service + '@' + self.host, str(self.port)],
                                       stdin = subprocess.PIPE,
                                       stdout = subprocess.PIPE,
                                       stderr = subprocess.PIPE)
        except OSError, e:
            raise httplib.NotConnected(e)

        self.sock = ProcessWrapper(process)
        self._process = process

    def getError(self):
        return self._process.stderr.read()


class KNCHTTPConnection(WrappedHTTPConnection):

    KNC_PATH = '/ms/dist/kerberos/PROJ/knc/prod/bin/knc'

    def __init__(self, host, port, service, strict = None):
        WrappedHTTPConnection.__init__(self, self.__class__.KNC_PATH,
                                       host, port, service, strict)
