# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015,2016  Contributor
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
from aquilon.exceptions_ import InternalError

LOGGER = logging.getLogger(__name__)


class ExportHandler(object):
    """
    Handle the creation of export events.

    Implementers should inherit from this class in order to hook into lifecycle
    events within the broker.  To acheive this the class needs to be registered
    with the Exporter using either the register_exporter decorator or the
    Exporter.register class method (see the latter for the calling convention).
    """

    def create(self, obj, **kwargs):
        """Called when an object is created."""
        pass

    def update(self, obj, **kwargs):
        """Called when an object is updated."""
        pass

    def delete(self, obj, **kwargs):
        """Called when an object is deleted."""
        pass

    def publish(self, notifications, **kwargs):
        """Called by the Exporter to emmit the notifications"""
        raise NotImplementedError


class ExporterNotification(object):
    """
    Exporter Notification

    Like the transaction this should be subclassed by implementers.  The publish
    method of the handler will be called with a list of notifications.
    """
    pass


class Exporter(object):
    """
    Exporter

    The exporter manages notifications for ExportHandler classes
    (see above).  ExportHandler are registed as follow:

        @register_exporter('SomeClass')
        class SomeClassExporter(ExportHandler):
            ...

    The constructor of the Exporter will save all of the kwargs and pass them
    to all of the various methods of the above classes.
    """

    # Dictoionary of handlers indexed by the class name.  Each entry
    # contains a list of the handlers for the given class type.
    _handlers = defaultdict(list)

    @classmethod
    def register(cls, handler, *cls_names):
        """
        Resgister an ExportHandler for the given class types.  This method should
        be called durning initalisation to register the handler.
        """
        if not isinstance(handler, ExportHandler):
            raise InternalError('Handler must be of type ExportHandler')
        for cls_name in cls_names:
            cls._handlers[cls_name].append(handler)

    def __init__(self, **kwargs):
        """
        Create a new exporter instance.  The exporter class should be used by
        BrokerCommand's to facilite the export of data to other systems.  The
        contents of kwargs will be passed to the methods of registered
        ExportHandler classes.  If kwargs contrains 'logger' then this will
        be used as the logger object for this class.
        """
        self._kwargs = kwargs
        # Indexed by handler, contains notifications
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
        else:
            raise InternalError('ExportHandler returned an unknown action')

    # Handle the create and delete methods; they are essentially the same
    # so method implements the common functionality.
    def _do_create_or_delete(self, task, obj):
        for name in [c.__name__ for c in obj.__class__.__mro__]:
            if name not in self._handlers:
                continue
            for handler in self._handlers[name]:
                action = getattr(handler, task)(obj, **self._kwargs)
                self._queue_action(handler, action)

    def create(self, obj):
        """
        Indicate that the passed object has been created
        """
        self._do_create_or_delete('create', obj)

    def update(self, obj):
        """
        Indicate that the passed object has been updated.
        """
        for oname in [c.__name__ for c in obj.__class__.__mro__]:
            if oname not in self._handlers:
                continue
            oid = id(obj)
            for handler in self._handlers[oname]:
                action = handler.update(obj, **self._kwargs)
                self._queue_action(handler, action)

    def delete(self, obj):
        """
        Indicate that the object has been deleted.
        """
        self._do_create_or_delete('delete', obj)

    def publish(self):
        """
        Publish any queued notifications
        """
        for handler, actions in self._actions.items():
            notificatons = actions['notifications']
            try:
                handler.publish(notificatons, **self._kwargs)
            except Exception as e:
                self._logger.info("Caught notification error: %s", e)

    # The following methods implment a context hander.  This can be used
    # to wrap the commit and rollback methods

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        # exc_type is !None if an exception occured
        if not exc_type:
            self.publish()


def register_exporter(*class_names):
    """
    Register an ExportHandler for the supplied class names.

    This decorator takes a list of classes (as arguments) and calls
    Exporter.register.
    """
    return lambda exporter: Exporter.register(exporter(), *class_names)


# Import all of the plugins
from aquilon.worker.exporters import *
