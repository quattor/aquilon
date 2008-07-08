#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon

import os

from twisted.internet import defer
from twisted.internet import reactor
from twisted.python import log

from aquilon.config import Config
from aquilon.server.authorization import AuthorizationBroker
from aquilon.exceptions_ import UnimplementedError
from aquilon.aqdb.db_factory import db_factory
from aquilon.server.formats.formatters import ResponseFormatter


class BrokerCommand(object):
    """ The basis for each command module under commands.
    
        In addition to the class, there are several decorators defined
        to enhance a command.  Since a command executes on its own
        thread, decorators are ideal - they will execute on the same
        thread as the command itself.

    """

    required_parameters = []
    """ This will generally be overridden by the command class
        definition.  It could theoretically be parsed out of input.xml,
        but that is tricky in some cases and possibly error-prone.

    """

    optional_parameters = []
    """ Optional parameters are filled in automatically when input.xml
        is parsed.  This may contain entries that are also in the
        required_parameters list.  If so, the required entry "wins".

    """

    def __init__(self):
        """ Provides some convenient variables for commands.  All of
            these objects are singletons (or Borg).
            
            Tried adding default decorators to the render() instance
            method here, but it does not seem to work.  There is some
            issue with self not being passed correctly.
        """
        self.dbf = db_factory()
        #self.dbf.meta.bind.echo = True
        self.config = Config()
        self.az = AuthorizationBroker()
        self.formatter = ResponseFormatter()
        # Force the instance to have local copies of the class defaults...
        # This allows resources.py to modify instances without worrying
        # about inheritance issues (classes sharing required or optional
        # parameters).
        self.required_parameters = self.required_parameters[:]
        self.optional_parameters = self.optional_parameters[:]

    def render(self, **arguments):
        """ Implement this method to create a functional broker command.
            The base __init__ method applies the add_transaction and
            az_check decorators to this method.

        """
        if self.__class__.__module__ == 'aquilon.server.broker':
            # Default class... no useful command info to repeat back...
            raise UnimplementedError("Command has not been implemented.")
        raise UnimplementedError("%s has not been implemented" %
                self.__class__.__module__)

def add_session(command):
    """Decorator to give any BrokerCommand a new session as a keyword arg.

       Any command using the @az_check should use @add_transaction instead
       of this, as @az_check may update the database.

    """
    def new_command(self, *args, **kwargs):
        if not "session" in kwargs:
            kwargs["session"] = self.dbf.session()
        return command(self, *args, **kwargs)
    new_command.__name__ = command.__name__
    new_command.__dict__ = command.__dict__
    new_command.__doc__ = command.__doc__
    return new_command

def add_transaction(command):
    """Decorator to give any BrokerCommand a new session as a keyword arg,
       and have the command execute within a transaction.

    """
    def new_command(self, *args, **kwargs):
        if not "session" in kwargs:
            kwargs["session"] = self.dbf.session()
        session = kwargs["session"]
        try:
            #session.begin() # Only required if session has transactional=False
            retval = command(self, *args, **kwargs)
            session.commit()
            return retval
        except:
            # Need to close after the rollback, or the next time session
            # is accessed it tries to commit the transaction... (?)
            session.rollback()
            session.close()
            raise
    new_command.__name__ = command.__name__
    new_command.__dict__ = command.__dict__
    new_command.__doc__ = command.__doc__
    return new_command

def az_check(command):
    """Decorator to add a basic authorization check to any BrokerCommand."""
    def new_command(self, *args, **kwargs):
        if not "session" in kwargs:
            kwargs["session"] = self.dbf.session()
        session = kwargs["session"]
        request = kwargs["request"]
        if not "user" in kwargs:
            kwargs["user"] = request.channel.getPrincipal()
        action = self.__module__
        if action.startswith("aquilon.server.commands."):
            action = action[24:]
        self.az.check(session, principal=kwargs["user"],
                action=action, resource=request.path)
        return command(self, *args, **kwargs)
    new_command.__name__ = command.__name__
    new_command.__dict__ = command.__dict__
    new_command.__doc__ = command.__doc__
    return new_command

def format_results(command):
    """Decorator to run the results of a BrokerCommand through the formatter."""
    def new_command(self, *args, **kwargs):
        results = command(self, *args, **kwargs)
        style = kwargs.get("style", None)
        request = kwargs["request"]
        return self.formatter.format(style, results, request)
    new_command.__name__ = command.__name__
    new_command.__dict__ = command.__dict__
    new_command.__doc__ = command.__doc__
    return new_command

# FIXME: This utility method may be better suited elsewhere.
def force_int(label, value):
    if value is None:
        return None
    try:
        result = int(value)
    except Exception, e:
        raise ArgumentError("Expected an integer for %s: %s" % (label, e))
    return result


