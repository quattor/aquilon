# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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
"""Pub/sub mechanism for status messages."""


from threading import Lock
from collections import deque
from logging import DEBUG

from twisted.internet import reactor

from aquilon.python_patches import load_uuid_quickly

uuid = load_uuid_quickly()  # pylint: disable=C0103


# Some requests can generate many debug messages.  After this limit is
# passed older records will be replaced with None.
# This is somewhat arbitrary as a number.  If each log message was a
# string of 100 bytes then 10000 would be about 1 MB.  However the log
# record object has quite a few more fields (source file, line, function
# name, and potentially exception info) which can bloat this quite a bit.
MAX_DEBUG_MESSAGES_PER_REQUEST = 10000


class RequestStatus(object):
    """Store status information for each incoming request.

    Each request will get one of these objects to write status
    information into.  Other commands (currently only show_request)
    can attach StatusSubscriber instances that will be called whenever
    new status info is available.  The info is stored as LogRecord
    objects from the python logging module.

    The initial implementation of this class used Condition objects to
    send notifications about available messages.  This caused two
    problems.  First and most important, deadlocks.  This code needs
    to work from threads that are themselves using lock mechanisms.
    Second, speed.  Anything beyond the simple Lock mechanism is
    implemented in python (that is, not natively).  Performance is
    horrible.

    The current implementation uses callbacks to reduce the number
    of threads touching this object.  Since there could be multiple
    threads we still need to lock operations that change internal
    state.  The lock in use is the primitive Lock provided by python.
    It is the only lock construct implemented natively in cPython
    (as of 2.5) - the rest are built on top of it.

    """

    def __init__(self, auditid, requestid=None):
        """Should only be created by the StatusCatalog."""
        self.auditid = str(auditid) if auditid is not None else None
        self.requestid = requestid
        self.user = ""
        self.command = ""
        self.args = []
        self.description = ""
        self.subscriber_descriptions = []
        self.records = []
        self.debug_fifo = deque()
        self.is_finished = False
        # Dict of subscribers to the length of the records list the last
        # time it was processed by the subscriber.
        self.subscribers = {}
        # This lock should be aquired for any access to records, is_finished,
        # or subscribers.
        # Need to be careful to be as fine-grained as possible.
        self.lock = Lock()

    def create_description(self, user, command, id, kwargs):
        massaged = []
        for (k, v) in kwargs.items():
            if k == 'format' and v == 'raw':
                continue
            if v == 'True':
                massaged.append(" --%s" % k)
            elif v is None:
                pass
            else:
                massaged.append(" --%s=%s" % (k, v))
        description = '[%s] %s: aq %s%s' % (id, user, command,
                                            "".join(massaged))
        if str(id) != self.auditid:
            self.subscriber_descriptions.append(description)
            return
        self.user = user
        self.command = command
        self.kwargs = kwargs
        self.description = description

    def publish(self, record):
        """Add a new message into the status log and notify watchers."""
        with self.lock:
            self.records.append(record)
            # Constrain the number of debug messages kept to keep memory
            # usage in check.
            if record.levelno <= DEBUG:
                self.debug_fifo.append(len(self.records) - 1)
                if len(self.debug_fifo) > MAX_DEBUG_MESSAGES_PER_REQUEST:
                    remove_index = self.debug_fifo.popleft()
                    self.records[remove_index] = None
            for (subscriber, processed) in self.subscribers.items():
                self._notify_subscriber(subscriber, processed)

    def add_subscriber(self, subscriber):
        """The subscriber should subclass/implement StatusSubscriber."""
        # Only need to lock the operations if not finished (more incoming
        # records expected).
        with self.lock:
            if not self.is_finished:
                self.subscribers[subscriber] = 0
                self._notify_subscriber(subscriber, processed=0)
                return
        self._notify_subscriber(subscriber, processed=0)
        subscriber.finish()

    def _notify_subscriber(self, subscriber, processed):
        # No lock in this method... it may not be necessary if the
        # messages are finished.  Lock is taken at a higher level when needed.
        known = len(self.records)
        for record_index in range(processed, known):
            record = self.records[record_index]
            # The record may have been replaced by None if too many
            # debug messages were seen.
            if record is not None:
                subscriber.process(record)
        if subscriber in self.subscribers:
            self.subscribers[subscriber] = known

    def finish(self):
        """Indicate that no more messages will be published."""
        with self.lock:
            self.is_finished = True
            while self.subscribers:
                (subscriber, processed) = self.subscribers.popitem()
                if processed < len(self.records):
                    self._notify_subscriber(subscriber, processed)
                subscriber.finish()


class StatusCatalog(object):
    """Global store for all StatusRequest objects."""

    __shared_state = {}

    status_by_auditid = {}
    status_by_requestid = {}

    def __init__(self):
        """Borg object."""
        self.__dict__ = self.__shared_state

    def get_request_status(self, auditid=None, requestid=None):
        """Retrieve a previously created RequestStatus."""
        status = None
        if auditid is not None:
            auditid = str(auditid)
            status = self.status_by_auditid.get(auditid)
        if not status and requestid in self.status_by_requestid:
            status = self.status_by_requestid.get(requestid)
        return status

    def create_request_status(self, auditid, requestid=None):
        """Create a new RequestStatus and store it."""
        if auditid is not None:
            auditid = str(auditid)
            if not requestid:
                requestid = uuid.uuid4()
            status = RequestStatus(auditid, requestid)
            self.status_by_requestid[requestid] = status
            self.status_by_auditid[auditid] = status
            return status
        return None

    def remove_by_auditid(self, status):
        """Mark the RequestStatus as finished and remove references to it."""
        status.finish()
        self.status_by_auditid.pop(status.auditid, None)
        # Clean up any unused requestid entries after one minute.
        reactor.callLater(60, self.remove_by_requestid, status)

    def remove_by_requestid(self, status):
        """Mark the RequestStatus as no longer needed by the client."""
        if status.requestid:
            self.status_by_requestid.pop(status.requestid, None)


class StatusSubscriber(object):
    """Objects that want to be notified of new records should subclass this."""

    def __init__(self):
        pass

    def process(self, record):  # pragma: no cover
        """Each record will be passed to process() as it comes in."""
        pass

    def finish(self):  # pragma: no cover
        """Called after all records have been processed."""
        pass
