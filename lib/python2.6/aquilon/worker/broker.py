# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
""" Module containing the base class BrokerCommand """

import sys
import re
from inspect import isclass

from sqlalchemy.sql import text
from twisted.web import http
from twisted.python import log

from aquilon.config import Config
from aquilon.exceptions_ import (ArgumentError, AuthorizationException,
                                 NotFoundException, UnimplementedError,
                                 PartialError, AquilonError)
from aquilon.worker.authorization import AuthorizationBroker
from aquilon.worker.messages import StatusCatalog
from aquilon.worker.logger import RequestLogger
from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model.xtn import start_xtn, end_xtn
from aquilon.worker.formats.formatters import ResponseFormatter
from aquilon.worker.dbwrappers.user_principal import (
        get_or_create_user_principal)
from aquilon.worker.dbwrappers.resources import add_resource, del_resource
from aquilon.locks import LockKey
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.templates.domain import TemplateDomain
from aquilon.worker.services import Chooser
from aquilon.worker.processes import sync_domain

# Things we don't need cluttering up the transaction details table
_IGNORED_AUDIT_ARGS = ('requestid', 'bundle', 'debug')

audit_id = 0
"""This will help with debugging active incoming requests.

   Eventually it will be replaced by a primary key in the audit log table.

   """

# Mapping of command exceptions to client return code.
ERROR_TO_CODE = {NotFoundException:http.NOT_FOUND,
                 AuthorizationException:http.UNAUTHORIZED,
                 ArgumentError:http.BAD_REQUEST,
                 UnimplementedError:http.NOT_IMPLEMENTED,
                 PartialError:http.MULTI_STATUS}

def get_code_for_error_class(e):
    if e is None or e == None.__class__:
        return http.OK
    return ERROR_TO_CODE.get(e, http.INTERNAL_SERVER_ERROR)


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

    parameter_checks = {}
    """ Parameter checks are filled in automatically based on input.xml.

    This lets us do some rudimentary checks before the actual command is
    invoked.

    """

    # The parameter types are filled in automatically based on input.xml.
    parameter_types = {}
    # This is the pivot of the above, filled in at the same time.  It is a
    # dictionary of type names to lists of parameters.
    parameters_by_type = {}

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

    # Override to indicate whether the command will generally take a
    # lock during execution.
    #
    # Any command with this flag set to True will use the separate
    # NLSession thread pool and should not have to wait on commands
    # that are potentially all blocking on the same lock.
    #
    # If set to None (the default), the is_lock_free property will
    # examine the command's module to try to determine if a lock
    # may be required and then cache the value.
    _is_lock_free = None

    # Run the render method on a separate thread.  This will be forced
    # to True if requires_azcheck or requires_transaction.
    defer_to_thread = True

    def __init__(self):
        """ Provides some convenient variables for commands.

        Also sets requires_* parameters for some sets of commands.
        All of the command objects are singletons (or Borg).

        """
        self.dbf = DbFactory()
        self.config = Config()
        self.az = AuthorizationBroker()
        self.formatter = ResponseFormatter()
        self.catalog = StatusCatalog()
        # Force the instance to have local copies of the class defaults...
        # This allows resources.py to modify instances without worrying
        # about inheritance issues (classes sharing required or optional
        # parameters).
        self.required_parameters = self.required_parameters[:]
        self.optional_parameters = self.optional_parameters[:]
        self.parameter_checks = self.parameter_checks.copy()
        self.action = self.__module__
        package_prefix = "aquilon.worker.commands."
        if self.action.startswith(package_prefix):
            self.action = self.action[len(package_prefix):]
        # self.command is set correctly in resources.py after parsing input.xml
        self.command = self.action
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
            self.requires_readonly = True
            self._is_lock_free = True
        if not self.requires_readonly \
           and self.config.get('broker', 'mode') == 'readonly':
            self.badmode = 'readonly'
        else:
            self.badmode = False
        self._update_render(self.render)
        if not self.defer_to_thread:
            if self.requires_azcheck or self.requires_transaction:
                self.defer_to_thread = True
                log.msg("Forcing defer_to_thread to True because of "
                        "required authorization or transaction for %s" %
                        self.command)
            # Not sure how to handle formatting with deferred...
            self.requires_format = False
        #free = "True " if self.is_lock_free else "False"
        #log.msg("is_lock_free = %s [%s]" % (free, self.command))

    def render(self, **arguments):  # pragma: no cover
        """ Implement this method to create a functional broker command.

        The base __init__ method wraps all implementations using
        _update_render() to enforce the class requires_* flags.

        """
        if self.__class__.__module__ == 'aquilon.worker.broker':
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
            principal = kwargs["user"]
            request = kwargs["request"]
            logger = kwargs["logger"]
            raising_exception = None
            try:
                if self.requires_transaction or self.requires_azcheck:
                    # Set up a session...
                    if not "session" in kwargs:
                        if self.is_lock_free:
                            kwargs["session"] = self.dbf.NLSession()
                        else:
                            kwargs["session"] = self.dbf.Session()
                    session = kwargs["session"]
                    dbuser = get_or_create_user_principal(session, principal,
                                                          commitoncreate=True)
                    kwargs["dbuser"] = dbuser
                    self._record_xtn(session, logger.get_status())

                    if self.requires_azcheck:
                        self.az.check(principal=principal, dbuser=dbuser,
                                      action=self.action,
                                      resource=request.path)

                    if self.requires_readonly:
                        self._set_readonly(session)
                    # begin() is only required if session transactional=False
                    #session.begin()
                if self.badmode: # pragma: no cover
                    raise UnimplementedError("Command %s not available on "
                                             "a %s broker." %
                                             (self.command, self.badmode))
                for key in kwargs.keys():
                    if key in self.parameter_checks:
                        kwargs[key] = self.parameter_checks[key]("--" + key,
                                                                 kwargs[key])
                # Command is an instance method already having self...
                retval = command(*args, **kwargs)
                if self.requires_format:
                    style = kwargs.get("style", None)
                    retval = self.formatter.format(style, retval, request)
                if "session" in kwargs:
                    session.commit()
                return retval
            except Exception, e:
                raising_exception = e
                # Need to close after the rollback, or the next time session
                # is accessed it tries to commit the transaction... (?)
                if "session" in kwargs:
                    session.rollback()
                    session.close()
                raise
            finally:
                # Obliterating the scoped_session - next call to session()
                # will create a new one.
                if "session" in kwargs:
                    # Complete the transaction
                    end_xtn(session, {'xtn_id': kwargs['requestid'],
                                      'return_code': get_code_for_error_class(
                                        raising_exception.__class__)})
                    if self.is_lock_free:
                        self.dbf.NLSession.remove()
                    else:
                        self.dbf.Session.remove()
                self._cleanup_logger(kwargs)
        updated_render.__name__ = command.__name__
        updated_render.__dict__ = command.__dict__
        updated_render.__doc__ = command.__doc__
        instancemethod = type(BrokerCommand.render)
        self.render = instancemethod(updated_render, self, BrokerCommand)

    def _set_readonly(self, session):
        if self.config.get("database", "dsn").startswith("oracle"):
            session.commit()
            session.execute(text("set transaction read only"))

    def _add_audit_id(self, request):
        global audit_id
        audit_id += 1
        request.aq_audit_id = audit_id

    def _audit(self, **kwargs):
        logger = kwargs.pop('logger')
        status = kwargs.pop('message_status')
        session = kwargs.pop('session', None)
        request = kwargs.pop('request')
        user = kwargs.pop('user', None)
        # Log a dummy user with no realm for unauthenticated requests.
        if user is None or user == '':
            user = 'nobody'
        dbuser = kwargs.pop('dbuser', None)
        kwargs['format'] = kwargs.pop('style', 'raw')

        for (key, value) in kwargs.items():
            if key in _IGNORED_AUDIT_ARGS:
                kwargs.pop(key)
                continue
            if value is None:
                kwargs.pop(key)
                continue
            if len(str(value)) > 100:
                kwargs[key] = value[0:96] + '...'
        kwargs_str = str(kwargs)
        if len(kwargs_str) > 1024:
            kwargs_str = kwargs_str[0:1020] + '...'
        logger.info("Incoming command #%d from user=%s aq %s "
                    "with arguments %s",
                    request.aq_audit_id, user, self.command, kwargs_str)
        if status:
            status.create_description(user=user, command=self.command,
                                      id=request.aq_audit_id,
                                      kwargs=kwargs)

    # This is meant to be called before calling render() in order to
    # add a logger into the argument list.  It returns the arguments
    # that will be passed into render().
    def add_logger(self, **command_kwargs):
        request = command_kwargs.get("request")
        command_kwargs["user"] = request.channel.getPrincipal()
        self._add_audit_id(request)
        if self.command == "show_request":
            status = self.catalog.get_request_status(
                auditid=command_kwargs.get("auditid", None),
                requestid=command_kwargs.get("requestid", None))
        else:
            status = self.catalog.create_request_status(
                auditid=request.aq_audit_id,
                requestid=command_kwargs.get("requestid", None))
            # If no requestid was given, the RequestStatus object created it.
            command_kwargs['requestid'] = status.requestid
        logger = RequestLogger(status=status, module_logger=self.module_logger)
        command_kwargs["logger"] = logger
        self._audit(message_status=status, **command_kwargs)
        return command_kwargs

    def _cleanup_logger(self, command_kwargs):
        logger = command_kwargs.get("logger", None)
        if logger:
            if self.command == "show_request":
                # Clear the requestid dictionary.
                logger.remove_status_by_requestid(self.catalog)
            else:
                # Clear the auditid dictionary.
                logger.debug("Server finishing request.")
                logger.remove_status_by_auditid(self.catalog)
            logger.close_handlers()

    def _record_xtn(self, session, status):
        audit_msg = dict()
        audit_msg['xtn_id'] = status.requestid
        audit_msg['username'] = status.user
        audit_msg['command'] = status.command
        audit_msg['readonly'] = self.requires_readonly

        details = dict()
        for k, v in status.kwargs.items():
            # Skip uber-redundant raw format parameter
            if (k == 'format') and v == 'raw':
                continue
            # Sometimes we delete a value and the arg comes in as an empty
            # string.  Denote this with a dash '-' to work around Oracle
            # not being able to store the concept of a non-NULL empty string.
            if v == '':
                v = '-'
            details[k] = str(v)
        audit_msg['details'] = details
        start_xtn(session, audit_msg, self.parameters_by_type.get('file'))

    @property
    def is_lock_free(self):
        if self._is_lock_free is None:
            self._is_lock_free = self.is_class_lock_free()
        return self._is_lock_free

    # A set of heuristics is provided as a default that works well
    # enough for most commands to set the _is_lock_free flag used
    # above.
    #
    # If the module has a Plenary class or a LockKey class imported it
    # is a good indication that a lock will be taken.
    #
    # This can be overridden per-command if general heuristics are not
    # enough.  This algorithm accounts for aliased (subclassed)
    # commands like reconfigure by calling this method on the superclass.
    # There is also an override in __init__ for the cat commands since
    # they all use Plenary classes but do not require a lock.
    @classmethod
    def is_class_lock_free(cls):
        #log.msg("Checking %s" % cls.__module__)
        for (key, item) in sys.modules[cls.__module__].__dict__.items():
            #log.msg("  Checking %s" % item)
            if item in [sync_domain, TemplateDomain,
                        add_resource, del_resource]:
                return False
            if not isclass(item):
                continue
            if issubclass(item, Plenary) or issubclass(item, Chooser) or \
               issubclass(item, LockKey) or \
               issubclass(item, PlenaryCollection):
                return False
            if item != cls and item != BrokerCommand and \
               issubclass(item, BrokerCommand):
                if item.__module__ not in sys.modules:
                    log.msg("Cannot evaluate %s, too early." % cls)
                    return False
                if item._is_lock_free is not None:
                    super_is_free = item._is_lock_free
                else:
                    super_is_free = item.is_class_lock_free()
                #log.msg("%s says %s" % (item, super_is_free))
                # If the superclass needs a lock, we need a lock.
                # However, if the superclass does not need a lock, keep
                # checking in case the subclass imports something else
                # that requires a lock.
                if not super_is_free:
                    return super_is_free
        return True

    @classmethod
    def deprecated_command(cls, msg, logger=None, user=None, **kwargs):
        if not logger or not user:  # pragma: no cover
            raise AquilonError("Too few arguments to deprecated_command")

        # cls.__name__ is good enough to mine the logs which deprecated commands
        # are still in use.
        logger.info("User %s invoked deprecated command %s" % (user,
                                                                cls.__name__))
        logger.client_info(msg)

    @classmethod
    def deprecated_option(cls, option, msg="", logger=None, user=None, **kwargs):
        if not option or not logger or not user:  # pragma: no cover
            raise AquilonError("Too few arguments to deprecated_option")

        # cls.__name__ is good enough to mine the logs which deprecated options
        # are still in use.
        logger.info("User %s used deprecated option %s of command %s" %
                    (user, option, cls.__name__))
        logger.client_info("The --%s option is deprecated.  %s" % (option, msg))


# This might belong somewhere else.  The functionality that uses this
# might end up in aqdb (in a similar class as AqStr).
# What is considered valid here should also be a valid nlist key.
basic_validation_re = re.compile('^[a-zA-Z_][a-zA-Z0-9_.-]*$')
"""Restriction for certain incoming labels beyond AqStr."""

def validate_basic(label, value):
    if not basic_validation_re.match(value):
        raise ArgumentError("'%s' is not a valid value for %s" %
                            (value, label))
