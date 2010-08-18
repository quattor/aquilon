# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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

from ipaddr import IPv4Address, IPv4IpValidationError
from aquilon.exceptions_ import ArgumentError

ratio_re = re.compile('^\s*(?P<left>\d+)\s*(?:[:/]\s*(?P<right>\d+))?\s*$')
yes_re = re.compile("^(true|yes|y|1|on|enabled)$", re.I)
no_re = re.compile("^(false|no|n|0|off|disabled)$", re.I)

def kill_from_pid_file(pid_file):
    if os.path.isfile(pid_file):
        f = open(pid_file)
        p = f.read()
        f.close()
        pid = int(p)
        print 'killing pid %s'%(pid)
        try:
            os.kill(pid, signal.SIGQUIT)
        except Exception,e:
            pass

def monkeypatch(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator

def confirm(prompt=None, resp=False):
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
    except IPv4IpValidationError, e:
        raise ArgumentError("Expected an IPv4 address for %s: %s" % (label, e))

def force_int(label, value):
    """Utility method to force incoming values to int and wrap errors."""
    if value is None:
        return None
    try:
        result = int(value)
    except ValueError, e:
        raise ArgumentError("Expected an integer for %s." % label)
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


class StateEngine:
    transitions = {} # Override in derived class!

    def transition(self, session, obj, to):
        '''Transition to another state.

        session -- the sqlalchemy session
        host -- the object which wants to change state
        to -- the target state name

        returns a list of objects that have changed state.
        throws an ArgumentError exception if the state cannot
        be reached. This method may be subclassed by states
        if there is special logic regarding the transition.
        If the current state has an onLeave method, then the
        method will be called with the object as an argument.
        If the target state has an onEnter method, then the
        method will be called with the object as an argument.

        '''

        #cls = self.__class__
        # This is truly horrible. We are given a subclass
        # as our query (e.g. "Ready"), but SQLalchemy needs the
        # parent class (e.g. "Status") in order to properly be
        # able to query all the other subclasses.
        # I can't find a way of getting the name
        # of the (appropriate) superclass in python, so I have
        # to pick a random class from the MRO. Well, it's not
        # random, but it feels like it :(
        import inspect
        cls = inspect.getmro(self.__class__)[1]
        ret = cls.get_unique(session, to, compel=True)
        to = ret.name
        if to == self.name:
            return False

        if to not in self.__class__.transitions:
            raise ArgumentError("status of %s is invalid" % to)

        targets = self.__class__.transitions[self.name]
        if to not in targets:
            raise ArgumentError(("cannot change state to %s from %s. " +
                   "Legal states are: %s") % (to, self.name,
                   ", ".join(targets)))

        if hasattr(self, 'onLeave'):
            self.onLeave(obj)
        obj.status = ret
        session.add(obj)
        if hasattr(ret, 'onEnter'):
            ret.onEnter(obj)
        return True
