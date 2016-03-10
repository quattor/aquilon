# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
"""
Export data to systems outside of the broker.
"""

import logging
from collections import defaultdict
from aquilon.exceptions_ import InternalError, RollbackException

LOGGER = logging.getLogger(__name__)

"""
Handle the creation of export events.

Implementers should inherit from this class in order to hook into lifecycle
events within the broker.  To acheive this the class needs to be registered
with the Exporter using either the register_exporter decorator or the
Exporter.register class method (see the latter for the calling convention).

Each of the methods of this class should return either an ExporterTransaction
or a ExporterNotification, depending if external state is being modified, or
only notifications are required.  None may be returned is neithing is required.
"""
class ExportHandler(object):
    """Called when an object is created."""
    def create(self, obj, **kwargs):
        pass

    """Called when an object is updated."""
    def update(self, obj, **kwargs):
        pass

    """Called when an object is deleted."""
    def delete(self, obj, **kwargs):
        pass

    """Called by the Exporter to apply a transaction"""
    def commit(self, action, **kwargs):
        raise NotImplementedError

    """Called by the Exporter to undo a transaction"""
    def rollback(self, action, **kwargs):
        raise NotImplementedError

    """Called by the Exporter to emmit the notifications"""
    def publish(self, notifications, **kwargs):
        raise NotImplementedError


"""
Exporter Transaction

Implementers should inherit from this class in order to manage transactions
with external systems.  The exporter will call the handler commit method
for all of the transactions it has stored.  Any errors will cause the
corrisponding rollback method to be called.  On success the exporter will
the process all of the notifications has stored.
"""
class ExporterTransaction(object):
    pass

"""
Exporter Notification

Like the transaction this should be subclassed by implementers.  The publish
method of the handler will be called with a list of notifications.
"""
class ExporterNotification(object):
    pass

"""
Exporter

The exporter manages transactions and notifications for ExportHandler classes
(see above).  ExportHandler are registed as follow:

    @register_exporter('SomeClass')
    class SomeClassExporter(ExportHandler):
        ...

The constructor of the Exporter will save all of the kwargs and pass them
to all of the various methods of the above classes.
"""
class Exporter(object):
    # Dictoionary of handlers indexed by the class name.  Each entry
    # contains a list of the handlers for the given class type.
    _handlers = defaultdict(list)

    """
    Resgister an ExportHandler for the given class types.  This method should
    be called durning initalisation to register the handler.
    """
    @classmethod
    def register(self, handler, *cls_names):
        if not isinstance(handler, ExportHandler):
            raise InternalError('Handler must be of type ExportHandler')
        for cls_name in cls_names:
            self._handlers[cls_name].append(handler)

    """
    Create a new exporter instance.  The exporter class should be used by
    BrokerCommand's to facilite the export of data to other systems.  The
    contents of kwargs will be passed to the methods of registered
    ExportHandler classes.  If kwargs contrains 'logger' then this will
    be used as the logger object for this class.
    """
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        # Indexed by handler, contains transactions and notifications
        self._actions = defaultdict(lambda: defaultdict(list))
        self._stash = defaultdict(dict)
        self._logger = kwargs.get('logger', LOGGER)

    # Queue a up an action created by an ExportHandler.  Each even should be
    # None or a supported class depending on the type it will be queued up internally.
    def _queue_action(self, handler, action):
        if action is None:
            return
        if isinstance(action, ExporterNotification):
            self._actions[handler]['notifications'].append(action)
        elif isinstance(action, ExporterTransaction):
            self._actions[handler]['transactions'].append(action)
        else:
            raise InternalError('ExportHandler returned an unknown action')

    # Handle the create and delete methods; they are essentially the same
    # so method implements the common functionality.
    def _do_create_or_delete(self, task, obj):
        name = obj.__class__.__name__
        if name in self._handlers:
            for handler in self._handlers[name]:
                action = getattr(handler, task)(obj, **self._kwargs)
                self._queue_action(handler, action)

    """
    Indicate that the passed object has been created
    """
    def create(self, obj):
        self._do_create_or_delete('create', obj)

    """
    Indicate that the passed object has been updated.
    """
    def update(self, obj):
        oname = obj.__class__.__name__
        oid = id(obj)
        if oname in self._handlers:
            for handler in self._handlers[oname]:
                hname = handler.__class__.__name__
                action = handler.update(obj, **self._kwargs)
                self._queue_action(handler, action)

    """
    Indicate that the object has been deleted.
    """
    def delete(self, obj):
        self._do_create_or_delete('delete', obj)

    """
    Commit the changes
    """
    def commit(self):
        for handler, actions in self._actions.items():
            transactions = actions['transactions']
            rollback = actions['rollback']
            for action in transactions:
                # Exceptions in the following are propergated
                handler.commit(action, **self._kwargs)
                rollback.append(action)

    """
    Publish any queued notifications
    """
    def publish(self):
        for handler, actions in self._actions.items():
            notificatons = actions['notifications']
            try:
                handler.publish(notificatons, **self._kwargs)
            except Exception as e:
                self._logger.info("Caught notification error: %s", e)

    """
    Perform any rollback opperations
    """
    def rollback(self):
        undo_failed = False
        for handler, actions in self._actions.items():
            rollback = actions['rollback']
            for action in rollback.reverse():
                try:
                    handler.rollback(action, **self._kwargs)
                except Exception as e:
                    self._logger.warning('Caught exporter rollback error: %s', e)
                    undo_failed = True

        if undo_failed:
            raise RollbackException()

    # The following methods implment a context hander.  This can be used
    # to wrap the commit and rollback methods

    def __enter__(self):
        try:
            self.commit()
        except Exception as e:
            self._logger.info("Exporter commit failed: %s", e)
            self.rollback()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # exc_type is !None if an exception occured
        if exc_type:
            self.rollback()
        else:
            self.publish()

    """
    The following method is called by the ORM when session.flush() is called.
    Internally this calls create, update and delete on the modified objects
    as required.
    """
    def event_after_flush(self, session, flush_context):
        for obj in session.new:
            self.create(obj)
        for obj in session.dirty:
            self.update(obj)
        for obj in session.deleted:
            self.delete(obj)


"""
Register an ExportHandler for the supplied class names.

This decorator takes a list of classes (as arguments) and calls
Exporter.register.
"""
def register_exporter(*class_names):
    return (lambda exporter: Exporter.register(exporter(), *class_names))


# Import all of the plugins
from aquilon.worker.exporters import *

