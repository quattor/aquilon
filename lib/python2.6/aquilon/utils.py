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
"""
    Useful subroutines that don't fit in any place to particularly for aquilon.

    Copyright (C) 2008 Morgan Stanley
    This module is part of Aquilon
"""
import os
import signal
import re
import json

from ipaddr import IPv4Address, AddressValueError
from aquilon.exceptions_ import ArgumentError

ratio_re = re.compile('^\s*(?P<left>\d+)\s*(?:[:/]\s*(?P<right>\d+))?\s*$')
yes_re = re.compile("^(true|yes|y|1|on|enabled)$", re.I)
no_re = re.compile("^(false|no|n|0|off|disabled)$", re.I)
_unpadded_re = re.compile(r'\b([0-9a-f])\b')
_nocolons_re = re.compile(r'^([0-9a-f]{2}){6}$')
_two_re = re.compile(r'[0-9a-f]{2}')
_padded_re = re.compile(r'^([0-9a-f]{2}:){5}([0-9a-f]{2})$')


def kill_from_pid_file(pid_file):  # pragma: no cover
    if os.path.isfile(pid_file):
        f = open(pid_file)
        p = f.read()
        f.close()
        pid = int(p)
        print 'Killing pid %s' % pid
        try:
            os.kill(pid, signal.SIGQUIT)
        except OSError, err:
            print 'Failed to kill %s: %s' % (pid, err.strerror)


def monkeypatch(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator


def confirm(prompt=None, resp=False):  # pragma: no cover
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [y]|n:
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y:
    False
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: y
    True

    """

    if prompt is None:
        prompt = 'Confirm'

    if resp:
        prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
    else:
        prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')

    while True:
        ans = raw_input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'yes', 'n', 'N', 'no']:
            print 'please enter y or n.'
            continue
        if ans == 'y' or ans == 'Y' or ans == 'yes':
            return True
        if ans == 'n' or ans == 'N' or ans == 'no':
            return False


def force_ipv4(label, value):
    if value is None:
        return None
    if isinstance(value, IPv4Address):
        return value
    try:
        return IPv4Address(value)
    except AddressValueError, e:
        raise ArgumentError("Expected an IPv4 address for %s: %s" % (label, e))


def force_int(label, value):
    """Utility method to force incoming values to int and wrap errors."""
    if value is None:
        return None
    try:
        result = int(value)
    except ValueError:
        raise ArgumentError("Expected an integer for %s." % label)
    return result


def force_float(label, value):
    """Utility method to force incoming values to float and wrap errors."""
    if value is None:
        return None
    try:
        result = float(value)
    except ValueError:
        raise ArgumentError("Expected an floating point number for %s." % label)
    return result


def force_ratio(label, value):
    """Utility method to force incoming values to int ratio and wrap errors."""
    if value is None:
        return (None, None)
    m = ratio_re.search(value)
    if not m:
        raise ArgumentError("Expected a ratio like 1:2 for %s but got '%s'" %
                            (label, value))
    (left, right) = m.groups()
    if right is None:
        right = 1
    return (int(left), int(right))


def force_boolean(label, value):
    """Utility method to force incoming values to boolean and wrap errors."""
    if value is None:
        return None
    if yes_re.match(value):
        return True
    if no_re.match(value):
        return False
    raise ArgumentError("Expected a boolean value for %s." % label)


def force_mac(label, value):
    # Allow nullable Mac Addresses, consistent with behavior of IPV4
    if value is None:
        return None

    # Strip, lower, and then use a regex for zero-padding if needed...
    value = _unpadded_re.sub(r'0\1', str(value).strip().lower())
    # If we have exactly twelve hex characters, add the colons.
    if _nocolons_re.search(value):
        value = ":".join(_two_re.findall(value))
    # Check to make sure we're good.
    if _padded_re.search(value):
        return value
    raise ArgumentError("Expected a MAC address like 00:1a:2b:3c:0d:55, "
                        "001a2b3c0d55 or 0:1a:2b:3c:d:55 for %s." % label)


def force_ascii(label, value):
    if value is None:
        return None
    try:
        value = value.decode('ascii')
    except UnicodeDecodeError:
        raise ArgumentError("Only ASCII characters are allowed for %s." % label)
    return value


def force_list(label, value):
    """
    Convert a value containing embedded newlines to a list.

    The function also removes empty lines and lines starting with '#'.
    """
    if value is None:
        return None
    lines = map(lambda x: force_ascii('line', x.strip()), value.splitlines())
    return filter(lambda x: x and not x.startswith("#"), lines)


def force_json_dict(label, value):
    if value is None:
        return None
    try:
        value = json.loads(value)
    except ValueError, e:
        raise ArgumentError("The json string specified for %s is invalid : %s"
                            % (label, e))
    return value


def first_of(iterable, function):
    """
    Return the first matching element of an iterable

    This function is useful if you already know there is at most one matching
    element.
    """
    for item in iterable:
        if function(item):
            return item
    return None
