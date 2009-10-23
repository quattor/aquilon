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
"""Exceptions to be used by Aquilon"""
"""The base exception class is AquilonError."""

def deprecated(message):
    import warnings
    warnings.warn(message, DeprecationWarning, stacklevel=2)


class AquilonError(StandardError):
    '''Generic error class.'''


class ArgumentError(AquilonError):
    """Raised for all those conditions where invalid arguments are
    sent to constructed objects.  This error generally corresponds to
    construction time state errors.

    """


class ProtocolError(AquilonError):
    """Raised when an import of a protocol fails

    """


class ProcessException(AquilonError):
    """Raised when a process being executed fails."""
    def __init__(self, command=None, out=None, err=None,
            code=None, signalNum=None):
        self.command = command
        self.out = out
        self.err = err
        self.code = code
        self.signalNum = signalNum
        if command:
            msg = "Command '%s' failed" % command
        else:
            msg = "Command failed"
        if code:
            msg = msg + " with return code '%d'" % code
        elif signalNum:
            msg = msg + " with signal '%d'" % signalNum
        if err and err.strip():
            msg = msg + " and stderr:\n%s" % err
        elif out and out.strip():
            msg = msg + " and stdout:\n%s" % out
        StandardError.__init__(self, msg)


class RollbackException(AquilonError):
    """If this is being thrown, should attempt to rollback any high-level
    activities being executed."""
    # This isn't fully baked yet... might not be necessary.
    def __init__(self, jobid=None, cause=None, *args, **kwargs):
        self.jobid = jobid
        self.cause = cause
        if not args and cause:
            args = [ str(cause) ]
        AquilonError.__init__(self, *args, **kwargs)


class AuthorizationException(AquilonError):
    """Raised when a principle is not authorized to perform a given
    action on a resource.

    """


class NotFoundException(AquilonError):
    """Raised when a requested resource cannot be found."""


class NameServiceError(AquilonError):
    """Raised when a host or service name cannot be found, or differs from,
    what's stored in name services such as dns."""


class UnimplementedError(AquilonError):
    """Raised when a command has not been implemented."""


class IncompleteError(AquilonError):
    """Raised when an incomplete/unusable template would be generated."""


class DetailedProcessException(AquilonError):
    """Raised when more details about a process exception should
    be shown to the client.

    """

    def __init__(self, pe, input=None, output=None):
        self.processException = pe
        self.output = output
        msg = str(pe) + "\n"
        if input:
            msg = msg + "\ninput:\n" + input + "\n"
        if output:
            msg = msg + "\nstdout:\n" + output + "\n"
        elif pe.out:
            msg = msg + "\nstdout:\n" + pe.out + "\n"
        if pe.err:
            msg = msg + "\nstderr:\n" + pe.err + "\n"
        AquilonError.__init__(self, msg)


class PartialError(AquilonError):
    """Raised when a batch job has some failures."""

    def __init__(self, success, failed, success_msg=None, failed_msg=None):
        msg = []
        if success_msg:
            msg.append(success_msg)
        else:
            msg.append("The following were successful:")
        msg.extend(success)
        if failed_msg:
            msg.append(failed_msg)
        else:
            msg.append("The following failed:")
        msg.extend(failed)
        AquilonError.__init__(self, "\n".join(msg))


class InternalError(AquilonError):
    """Raised when an algorithm error or internal data corruption is seen.

    These should only be raised from "can't happen" code and are
    preferred over assertion errors.
    """


