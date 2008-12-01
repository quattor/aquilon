# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon


import os

from sqlalchemy.sql import text
from twisted.internet import defer
from twisted.internet import reactor
from twisted.python import log

from aquilon.config import Config
from aquilon.exceptions_ import ArgumentError, UnimplementedError
from aquilon.server.authorization import AuthorizationBroker
from aquilon.aqdb.db_factory import db_factory
from aquilon.server.formats.formatters import ResponseFormatter


class BrokerCommand(object):
    """ The basis for each command module under commands.

    Several class-level lists and flags are defined here that can be
    overridden on a per-command basis.  Some can only be overridden
    in __init__, though, so check the docstrings.

    """

    required_parameters = []
    """ This will generally be overridden in the command class.

    It could theoretically be parsed out of input.xml, but that is
    tricky in some cases and possibly error-prone.

    """

    optional_parameters = []
    """ Optional parameters are filled in automatically from input.xml.

    This may contain entries that are also in the required_parameters list.
    If so, the required entry "wins".

    """

    requires_azcheck = True
    """ Opt out of authorization checks by setting this flag to False."""

    requires_transaction = True
    """ This sets up a session and cleans up when finished.

    Currently, setting azcheck to True will force this value to be True,
    because the azcheck requires a session that will need to be cleaned
    up.

    """

    requires_format = False
    """ Run command results through the formatter.

    It is automatically set to True for all cat, search, and show
    commands, but could be reversed back to False by overriding __init__
    for the command.

    """

    requires_readonly = False
    """ Require read only isolation level for the render session.

    It is automatically set to True for all search and show commands,
    but could be reversed back to False by overriding __init__ for the
    command.

    """

    def __init__(self):
        """ Provides some convenient variables for commands.

        Also sets requires_* parameters for some sets of commands.
        All of the command objects are singletons (or Borg).

        """
        self.dbf = db_factory()
        self.config = Config()
        self.az = AuthorizationBroker()
        self.formatter = ResponseFormatter()
        # Force the instance to have local copies of the class defaults...
        # This allows resources.py to modify instances without worrying
        # about inheritance issues (classes sharing required or optional
        # parameters).
        self.required_parameters = self.required_parameters[:]
        self.optional_parameters = self.optional_parameters[:]
        self.action = self.__module__
        package_prefix = "aquilon.server.commands."
        if self.action.startswith(package_prefix):
            self.action = self.action[len(package_prefix):]
        # The readonly and format flags are done here for convenience
        # and simplicity.  They could be overridden by the __init__
        # method of any show/search/cat commands that do not want these
        # defaults.  Some 'one-off' commands (like ping and status)
        # just set the variables themselves.
        if self.action.startswith("show") or self.action.startswith("search"):
            self.requires_readonly = True
            self.requires_format = True
        if self.action.startswith("cat"):
            self.requires_format = True
        self._update_render(self.render)

    def render(self, **arguments):
        """ Implement this method to create a functional broker command.

        The base __init__ method wraps all implementations using
        _update_render() to enforce the class requires_* flags.

        """
        if self.__class__.__module__ == 'aquilon.server.broker':
            # Default class... no useful command info to repeat back...
            raise UnimplementedError("Command has not been implemented.")
        raise UnimplementedError("%s has not been implemented" %
                self.__class__.__module__)

    def _update_render(self, command):
        """ Wrap the render method using the requires_* attributes.

        An alternate implementation would be to just have a
        wrap_rendor() method or similar that got called instead
        of rendor().

        """
        def updated_render(self, *args, **kwargs):
            request = kwargs["request"]
            if not self.requires_transaction and not self.requires_azcheck:
                # These five lines are duped below... seemed like the
                # simplest way to code this method.
                retval = command(*args, **kwargs)
                if self.requires_format:
                    style = kwargs.get("style", None)
                    return self.formatter.format(style, retval, request)
                return retval
            if not "session" in kwargs:
                kwargs["session"] = self.dbf.session()
            session = kwargs["session"]
            if not "user" in kwargs:
                kwargs["user"] = request.channel.getPrincipal()
            if self.requires_azcheck:
                self.az.check(session, principal=kwargs["user"],
                              action=self.action, resource=request.path)
            self._audit(*args, **kwargs)
            if self.requires_readonly:
                self._set_readonly(session)
            try:
                # begin() is only required if session has transactional=False
                #session.begin()
                # Command is an instance method, and will already have self...
                retval = command(*args, **kwargs)
                session.commit()
                if self.requires_format:
                    style = kwargs.get("style", None)
                    return self.formatter.format(style, retval, request)
                return retval
            except:
                # Need to close after the rollback, or the next time session
                # is accessed it tries to commit the transaction... (?)
                session.rollback()
                session.close()
                raise
            finally:
                # Obliterating the scoped_session - next call to session()
                # will create a new one.
                self.dbf.Session.remove()
        updated_render.__name__ = command.__name__
        updated_render.__dict__ = command.__dict__
        updated_render.__doc__ = command.__doc__
        instancemethod = type(BrokerCommand.render)
        self.render = instancemethod(updated_render, self, BrokerCommand)

    def _set_readonly(self, session):
        if self.config.get("database", "dsn").startswith("oracle"):
            session.commit()
            session.execute(text("set transaction read only"))

    def _audit(self, *args, **kwargs):
        session = kwargs.pop('session')
        request = kwargs.pop('request')
        user = kwargs.pop('user', None)
        kwargs['aqformat'] = kwargs.pop('style', 'raw')
        # TODO: Have this less hard-coded...
        if self.action == 'put':
            kwargs.pop('bundle')
        # TODO: Something fancier...
        kwargs_str = str(kwargs)
        if len(kwargs_str) > 1024:
            kwargs_str = kwargs_str[0:1020] + '...'
        log.msg('command=%s user=%s args=%s kwargs=%s' %
                (self.action, user, args, kwargs_str))


# FIXME: This utility method may be better suited elsewhere.
def force_int(label, value):
    """Utility method to force incoming values to int and wrap errors."""
    if value is None:
        return None
    try:
        result = int(value)
    except Exception, e:
        raise ArgumentError("Expected an integer for %s: %s" % (label, e))
    return result


