# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011  Contributor
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


import logging
from threading import Condition

from aquilon.exceptions_ import InternalError

LOGGER = logging.getLogger('aquilon.locks')


class LockQueue(object):
    """Provide a layered (namespaced?) locking mechanism.

    When a lock request comes in it is put into a queue.  The lock
    request is made with an instance of LockKey.   Each key is a set
    of ordered components that describes a heirarchy.  The lock is
    granted once there are no conflicting lock requests preceeding
    it in the queue.

    As a convenience, ignore undefined keys.  This essentially
    equates a key of None with a no-op request.

    """

    def __init__(self):
        self.queue_condition = Condition()
        self.queue = []

    def acquire(self, key):
        if key is None:
            return
        key.transition("acquiring", debug=True)
        with self.queue_condition:
            if key in self.queue:
                raise InternalError("Duplicate attempt to aquire %s with the "
                                    "same key." % key)
            self.queue.append(key)
            while self.blocked(key):  # pragma: no cover
                key.log("requesting %s with %s others waiting",
                        key, key.blocker_count)
                self.queue_condition.wait()
            key.transition("acquired")

    def blocked(self, key):
        """Indicate whether the lock for this key can be acquired.

        As a side effect, reset the key's knowledge of external
        blockers and let it know if it is in line.

        """
        if key is None:
            return False
        key.reset_blockers()
        is_blocked = False
        for k in self.queue:
            if k == key:
                return is_blocked
            if k.blocks(key):
                key.register_blocker(k)
                is_blocked = True
        # Can only get here if the key is not in the queue - seems
        # like a valid theoretical question to ask - in which case
        # the method is "would queued keys block this one?"
        return is_blocked

    def release(self, key):
        if key is None:
            return
        key.transition("releasing")
        with self.queue_condition:
            self.queue.remove(key)
            self.queue_condition.notifyAll()
        key.transition("released", debug=True)


class LockKey(object):
    """Create a key composed of an ordered list of components.

    The intent is that this class is subclassed to take a dictionary
    and provide validation before setting the components variable.

    """

    def __init__(self, components, logger=LOGGER, loglevel=logging.INFO,
                 lock_queue=None):
        self.components = components
        self.logger = logger
        self.loglevel = loglevel
        self.blocker_count = None
        self.lock_queue = lock_queue
        self.transition("initialized", debug=True)

    def __str__(self):
        if not self.components:
            return 'lock'
        if len(self.components) == 1:
            return '%s lock' % self.components[0]
        return '%s lock for %s' % (self.components[0],
                                   "/".join(self.components[1:]))

    def __enter__(self):
        if not self.lock_queue:  # pragma: no cover
            raise InternalError("Using the 'with' statement requires a lock "
                                "queue")
        self.lock_queue.acquire(self)

    def __exit__(self, exc_type, exc_value, traceback):
        self.lock_queue.release(self)

    def log(self, *args, **kwargs):
        self.logger.log(self.loglevel, *args, **kwargs)

    def transition(self, state, debug=False):
        self.state = state
        if debug:
            self.logger.debug('%s %s', state, self)
        else:
            self.log('%s %s', state, self)

    def reset_blockers(self):
        self.blocker_count = 0

    def register_blocker(self, key):
        self.blocker_count += 1

    def blocks(self, key):
        """Determine if this key blocks another.

        The algorithm exploits the zip() implementation.  There are two
        basic cases:

        The keys are the same length.  They only block each other if
        they match exactly.  Using zip to interleave the parts for
        comparison should make sense here.  If any of the parts are
        not equal then the two keys do not conflict.

        The keys are different length.  Here, they block if one is
        a superset of the other.  That is, if the shorter keys matches
        all the components of the longer key.  The zip() method will
        truncate the comparison to the length of the shorter list.
        Thus the logic is the same - if all the paired components
        match then the keys are blocked.

        """

        for (a, b) in zip(self.components, key.components):
            if a != b:
                return False
        return True

    @staticmethod
    def merge(keylist):
        """Find the common root of a list of keys and make a new key.

        The new key will be in the LockKey class.  Returning a key of
        the same class as the list (assuming they're all the same) is
        possible but more work for little gain.

        """
        keylist = [key for key in keylist if key is not None]
        if not keylist:
            return None
        components = []
        # Assume logger/loglevel is consistent across the list.
        logger = keylist[0].logger
        loglevel = keylist[0].loglevel
        lock_queue = keylist[0].lock_queue
        for position in zip(*[key.components for key in keylist]):
            unique_elements = set(position)
            if len(unique_elements) == 1:
                components.append(unique_elements.pop())
            else:
                return LockKey(components, logger=logger, loglevel=loglevel,
                               lock_queue=lock_queue)
        return LockKey(components, logger=logger, loglevel=loglevel,
                       lock_queue=lock_queue)
