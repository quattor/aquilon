# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014  Contributor
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


import logging
from threading import Condition
from collections import defaultdict
from itertools import chain

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
        key.transition("acquiring")
        with self.queue_condition:
            if key in self.queue:
                raise InternalError("Duplicate attempt to aquire %s with the "
                                    "same key." % key)
            self.queue.append(key)
            while self.blocked(key):  # pragma: no cover
                self.queue_condition.wait()
            key.transition("acquired")

    def blocked(self, key):
        """Indicate whether the lock for this key can be acquired.

        As a side effect, reset the key's knowledge of external
        blockers and let it know if it is in line.

        """
        blocker_count = 0
        for k in self.queue:
            if k == key:
                break
            blockers = k.blocks(key)
            if blockers:
                blocker_count += 1
                key.log("Blocking on %s" % ", ".join(sorted(list(blockers))))
        # Can only get here if the key is not in the queue - seems
        # like a valid theoretical question to ask - in which case
        # the method is "would queued keys block this one?"
        return blocker_count > 0

    def release(self, key):
        key.transition("releasing")
        with self.queue_condition:
            self.queue.remove(key)
            self.queue_condition.notifyAll()
        key.transition("released")


class LockKey(object):
    """Create a key composed of a bunch of unrelated items.

    The intent is that this class is subclassed to provide validation.

    """

    def __init__(self, logger=LOGGER, loglevel=logging.INFO,
                 lock_queue=None):
        self.shared = defaultdict(set)
        self.exclusive = defaultdict(set)
        self.logger = logger
        self.loglevel = loglevel
        self.lock_queue = lock_queue
        self.state = None

    def __str__(self):
        exc_items = []
        shared_items = []
        for name, items in self.exclusive.iteritems():
            exc_items.extend(["%s/%s" % (name, item) for item in items])

        for name, items in self.shared.iteritems():
            shared_items.extend(["%s/%s" % (name, item) for item in items])

        exc_items.sort()
        shared_items.sort()

        return "exclusive(%s), shared(%s)" % (", ".join(exc_items),
                                              ", ".join(shared_items))

    def __enter__(self):
        if not self.lock_queue:  # pragma: no cover
            raise InternalError("Using the 'with' statement requires a lock "
                                "queue")
        self.lock_queue.acquire(self)

    def __exit__(self, exc_type, exc_value, traceback):
        self.lock_queue.release(self)

    def log(self, *args, **kwargs):
        self.logger.log(self.loglevel, *args, **kwargs)

    def transition(self, state):
        # Sanity checking. Locks in the queue may be touched from other threads,
        # and if a key is a DB object, that may trigger trying to access the
        # underlying DB connection from the wrong thread, which in turn leads to
        # very "interesting" errors. So make sure only strings are used.
        if state == "initialized":
            for keys in chain(self.exclusive.itervalues(),
                              self.shared.itervalues()):
                for key in keys:
                    if not isinstance(key, basestring):
                        raise ValueError("Lock key contains %r" % key)

        self.state = state
        self.logger.debug('%s %s', state, self)

    def blocks(self, key):
        """Determine if this key blocks another.

        The other key is blocked if:
            - our exclusive set intersects with their shared or exclusive
            - our shared set intersects with their exclusive
        """

        blockers = set()

        for name, items in self.exclusive.iteritems():
            if name in key.exclusive:
                blockers.update(["%s/%s" % (name, item)
                                 for item in items & key.exclusive[name]])
            if name in key.shared:
                blockers.update(["%s/%s" % (name, item)
                                 for item in items & key.shared[name]])

        for name, items in self.shared.iteritems():
            if name in key.exclusive and items & key.exclusive[name]:
                blockers.update(["%s/%s" % (name, item)
                                 for item in items & key.exclusive[name]])

        return blockers

    @staticmethod
    def merge(keylist):
        """Find the common root of a list of keys and make a new key.

        The new key will be in the LockKey class.  Returning a key of
        the same class as the list (assuming they're all the same) is
        possible but more work for little gain.

        """
        # Assume logger/loglevel is consistent across the list.
        logger = keylist[0].logger
        loglevel = keylist[0].loglevel
        lock_queue = keylist[0].lock_queue
        merged = LockKey(logger=logger, loglevel=loglevel,
                         lock_queue=lock_queue)
        for key in keylist:
            for name, items in key.exclusive.iteritems():
                merged.exclusive[name] |= items
            for name, items in key.shared.iteritems():
                merged.shared[name] |= items

        # Normalization. If something is locked exclusively, then it makes no
        # sense to have the same item in the shared set as well.
        for name, items in merged.shared.iteritems():
            if name in merged.exclusive:
                items -= merged.exclusive[name]
        return merged
