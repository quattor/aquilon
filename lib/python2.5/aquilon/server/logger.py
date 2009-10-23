# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-


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


