# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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


from logging import Logger, Handler, addLevelName, NOTSET, DEBUG, INFO


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

    # These two methods could be refactored and made cleaner.  This works
    # but mixes dependencies in an odd way.
    def remove_status_by_auditid(self, catalog):
        for handler in self.get_handlers_with_status():
            catalog.remove_by_auditid(handler.status)
            self.removeHandler(handler)

    def remove_status_by_requestid(self, catalog):
        for handler in self.get_handlers_with_status():
            catalog.remove_by_requestid(handler.status)
            self.removeHandler(handler)

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
        if CLIENT_INFO >=self.getEffectiveLevel():
            apply(self._log, (CLIENT_INFO, msg, args), kwargs)


