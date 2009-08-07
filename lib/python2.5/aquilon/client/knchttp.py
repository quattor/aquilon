import httplib
import subprocess
import os
import sys

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

class WrappedHTTPConnection(httplib.HTTPConnection):

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
