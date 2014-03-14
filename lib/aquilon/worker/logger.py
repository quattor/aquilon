# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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


from logging import Logger, Handler, addLevelName, NOTSET


CLIENT_INFO = 25
addLevelName(CLIENT_INFO, 'CLIENT_INFO')


class CommandHandler(Handler):
    def __init__(self, module_logger):
        Handler.__init__(self, level=NOTSET)
        self.logger = module_logger

    def emit(self, record):
        self.logger.handle(record)


class StatusHandler(Handler):
    def __init__(self, status):
        Handler.__init__(self, level=NOTSET)
        self.status = status

    def emit(self, record):
        self.status.publish(record)


class RequestLogger(Logger):
    def __init__(self, status=None, module_logger=None):
        Logger.__init__(self, "logger")
        if module_logger:
            self.addHandler(CommandHandler(module_logger))
        if status:
            self.addHandler(StatusHandler(status))

    def get_handlers_with_status(self):
        return [handler for handler in self.handlers
                if isinstance(handler, StatusHandler)]

    def get_status(self):
        for handler in self.get_handlers_with_status():
            return handler.status
        return None

    def remove_request_status(self, catalog):
        for handler in self.get_handlers_with_status():
            catalog.remove_request_status(handler.status)
            self.removeHandler(handler)
            # We must call close() otherwise the handler will not be removed
            # from logging._handlers and logging._handlerList
            handler.close()

    def close_handlers(self):
        """This method must be called or the handlers will leak memory.

        One of the remove_status commands should be called first in
        order to correctly clean up the status object.

        """
        for handler in self.handlers[:]:
            self.removeHandler(handler)
            handler.close()

    def client_info(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'CLIENT_INFO'.

        These messages are higher than INFO but lower than WARNING.  While
        INFO level will only appear in the server logs the CLIENT_INFO
        level will also be sent out to the caller.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.client_info("Houston, we have a %s", "problem", exc_info=1)
        """
        if self.manager.disable >= CLIENT_INFO:
            return
        if CLIENT_INFO >= self.getEffectiveLevel():
            apply(self._log, (CLIENT_INFO, msg, args), kwargs)
