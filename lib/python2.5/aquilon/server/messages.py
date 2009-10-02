# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Pub/sub mechanism for status messages."""


from time import sleep


class RequestStatus(object):
    """Store status information for each incoming request.

    The initial implementation of this class used Condition objects to
    send notifications about available messages.  This caused two
    problems.  First and most important, deadlocks.  This code needs
    to work from threads that are themselves using lock mechanisms.
    Second, speed.  Anything beyond the simple Lock mechanism is
    implemented in python (that is, not natively).  Performance is
    horrible.

    """

    def __init__(self, auditid, requestid=None):
        """Should only be created by the StatusCatalog."""
        self.auditid = (auditid is not None) and str(auditid) or None
        self.requestid = requestid
        self.records = []
        self.is_finished = False

    def publish(self, record):
        """Add a new message into the status log and notify watchers."""
        self.records.append(record)

    def finish(self):
        """Indicate that no more messages will be published."""
        self.is_finished = True

    def get_new(self, known_length=0):
        """Retrieve latest index of new messages.

        Will block until there are new messages or until finished.  The
        return value is an index into self.messages.  Callers should
        loop over this method until self.is_finished passing back in the
        last value returned.

        See the show_request command implementation for an example.

        """
        # Block until messages has grown past known_length or finished
        if self.is_finished:
            return len(self.records)
        while not self.is_finished and known_length >= len(self.records):
            sleep(.1)
        return len(self.records)


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
            if requestid:
                status = RequestStatus(auditid, requestid)
                self.status_by_requestid[requestid] = status
            else:
                status = RequestStatus(auditid)
            self.status_by_auditid[auditid] = status
            return status
        return None

    def remove_by_auditid(self, status):
        """Mark the RequestStatus as finished and remove references to it."""
        status.finish()
        self.status_by_auditid.pop(status.auditid, None)

    def remove_by_requestid(self, status):
        """Mark the RequestStatus as no longer needed by the client."""
        if status.requestid:
            self.status_by_requestid.pop(status.requestid, None)


