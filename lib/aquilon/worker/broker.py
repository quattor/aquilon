# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
""" Module containing the base class BrokerCommand """

import sys
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
_IGNORED_AUDIT_ARGS = ('requestid', 'bundle', 'debug', 'session', 'dbuser')

__audit_id = 0
"""This will help with debugging active incoming requests.

   Eventually it will be replaced by a primary key in the audit log table.

   """

def next_audit_id():
    global __audit_id
    __audit_id += 1
    return __audit_id

# Mapping of command exceptions to client return code.
ERROR_TO_CODE = {NotFoundException: http.NOT_FOUND,
                 AuthorizationException: http.UNAUTHORIZED,
                 ArgumentError: http.BAD_REQUEST,
                 UnimplementedError: http.NOT_IMPLEMENTED,
                 PartialError: http.MULTI_STATUS}


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

        # Parameter checks are filled in automatically based on input.xml. This
        # lets us do some rudimentary checks before the actual command is
        # invoked.
        self.parameter_checks = {}

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

    def audit_result(self, session, key, value, **arguments):
        # We need a place to store the result somewhere until we can finish the
        # audit record. Use the request object for now.
        request = arguments["request"]
        if not hasattr(request, "_audit_result"):
            request._audit_result = []

        request._audit_result.append((key, value))

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

        def updated_render(self, user=None, request=None, requestid=None,
                           logger=None, session=None, **kwargs):
            raising_exception = None
            rollback_failed = False
            dbuser = None
            try:
                if self.requires_transaction or self.requires_azcheck:
                    # Set up a session...
                    if not session:
                        if self.is_lock_free:
                            session = self.dbf.NLSession()
                        else:
                            session = self.dbf.Session()

                    if session.bind.dialect.name == "oracle":
                        # Make the name of the command and the request ID
                        # available in v$session. Trying to set a value longer
                        # than the allowed length will generate ORA-24960, so
                        # do an explicit truncation.
                        conn = session.connection()
                        dbapi_con = conn.connection.connection
                        dbapi_con.action = str(self.action)[:32]
                        # TODO: we should include the command number as well,
                        # since that is easier to find in the logs
                        dbapi_con.clientinfo = str(requestid)[:64]

                    # This does a COMMIT, which in turn invalidates the session.
                    # We should therefore avoid looking up anything in the DB
                    # before this point which might be used later.
                    status = logger.get_status()
                    start_xtn(session, status.requestid, status.user,
                              status.command, self.requires_readonly,
                              kwargs, _IGNORED_AUDIT_ARGS)

                    dbuser = get_or_create_user_principal(session, user,
                                                          commitoncreate=True)

                    if self.requires_azcheck:
                        self.az.check(principal=user, dbuser=dbuser,
                                      action=self.action, resource=request.path)

                    if self.requires_readonly:
                        self._set_readonly(session)
                    # begin() is only required if session transactional=False
                    #session.begin()
                if self.badmode:  # pragma: no cover
                    raise UnimplementedError("Command %s not available on "
                                             "a %s broker." %
                                             (self.command, self.badmode))
                # Command is an instance method already having self...
                retval = command(user=user, dbuser=dbuser, request=request,
                                 requestid=requestid, logger=logger,
                                 session=session, **kwargs)
                if self.requires_format:
                    style = kwargs.get("style", None)
                    retval = self.formatter.format(style, retval, request)
                if session:
                    session.commit()
                return retval
            except Exception, e:
                raising_exception = e
                # Need to close after the rollback, or the next time session
                # is accessed it tries to commit the transaction... (?)
                if session:
                    try:
                        session.rollback()
                    except:  # pragma: no cover
                        rollback_failed = True
                        raise
                    session.close()
                raise
            finally:
                # Obliterating the scoped_session - next call to session()
                # will create a new one.
                if session:
                    # Complete the transaction. We really want to get rid of the
                    # session, even if end_xtn() fails
                    try:
                        if not rollback_failed:
                            # If session.rollback() failed for whatever reason,
                            # our best bet is to avoid touching the session
                            end_xtn(session, requestid,
                                    get_code_for_error_class(
                                        raising_exception.__class__),
                                    getattr(request, '_audit_result', None))
                    finally:
                        if self.is_lock_free:
                            self.dbf.NLSession.remove()
                        else:
                            self.dbf.Session.remove()
                if logger:
                    self._cleanup_logger(logger)
        updated_render.__name__ = command.__name__
        updated_render.__dict__ = command.__dict__
        updated_render.__doc__ = command.__doc__
        instancemethod = type(BrokerCommand.render)
        self.render = instancemethod(updated_render, self, BrokerCommand)

    def _set_readonly(self, session):
        if session.bind.dialect.name == "oracle" or \
           session.bind.dialect.name == "postgresql":
            session.commit()
            session.execute(text("set transaction read only"))

    def _audit(self, message_status, logger=None, request=None, user=None,
               **kwargs):
        # Log a dummy user with no realm for unauthenticated requests.
        if user is None or user == '':
            user = 'nobody'
        kwargs['format'] = kwargs.pop('style', 'raw')

        for (key, value) in kwargs.items():
            if key in _IGNORED_AUDIT_ARGS:
                kwargs.pop(key)
                continue
            if value is None:
                kwargs.pop(key)
                continue
            if isinstance(value, list):
                value_str = " ".join([str(item) for item in value])
            else:
                value_str = str(value)
            if len(value_str) > 100:
                kwargs[key] = value_str[0:96] + '...'
        kwargs_str = str(kwargs)
        if len(kwargs_str) > 1024:
            kwargs_str = kwargs_str[0:1020] + '...'
        logger.info("Incoming command #%d from user=%s aq %s "
                    "with arguments %s",
                    request.aq_audit_id, user, self.command, kwargs_str)
        if message_status:
            message_status.create_description(user=user, command=self.command,
                                              id=request.aq_audit_id,
                                              kwargs=kwargs)

    # This is meant to be called before calling render() in order to
    # add a logger into the argument list.  It returns the arguments
    # that will be passed into render().
    def add_logger(self, **command_kwargs):
        request = command_kwargs.get("request")
        command_kwargs["user"] = request.channel.getPrincipal()
        request.aq_audit_id = next_audit_id()
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
        # Sigh. command_kwargs might contain the key 'status', so we have to use
        # another name.
        self._audit(message_status=status, **command_kwargs)
        return command_kwargs

    def _cleanup_logger(self, logger):
        if self.command == "show_request":
            # Clear the requestid dictionary.
            logger.remove_status_by_requestid(self.catalog)
        else:
            # Clear the auditid dictionary.
            logger.debug("Server finishing request.")
            logger.remove_status_by_auditid(self.catalog)
        logger.close_handlers()

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
        if not logger:  # pragma: no cover
            raise AquilonError("Too few arguments to deprecated_command")

        # cls.__name__ is good enough to mine the logs which deprecated commands
        # are still in use.

        if not user:
            user = "anonymous"

        logger.info("User %s invoked deprecated command %s" % (user,
                                                               cls.__name__))
        logger.client_info(msg)

    @classmethod
    def deprecated_option(cls, option, msg="", logger=None, user=None, **kwargs):
        if not option or not logger:  # pragma: no cover
            raise AquilonError("Too few arguments to deprecated_option")

        if not user:
            user = "anonymous"

        # cls.__name__ is good enough to mine the logs which deprecated options
        # are still in use.
        logger.info("User %s used deprecated option %s of command %s" %
                    (user, option, cls.__name__))
        logger.client_info("The --%s option is deprecated.  %s" % (option, msg))

    @classmethod
    def require_one_of(cls, *args, **kwargs):
        if args:
            # Take 'args' as the list of keys that we are going to check
            # exist in 'kwargs', we will ignore any addition 'kwargs'
            count = sum([1 if kwargs.get(arg, None) else 0 for arg in args])
        else:
            # Make sure only one of the supplied arguments is set
            count = sum([1 if x else 0 for x in kwargs.values()])
        if count != 1:
            if args:
                names = ["--%s" % arg for arg in args]
            else:
                names = ["--%s" % arg for arg in kwargs.keys()]
            raise ArgumentError("Exactly one of %s should be sepcified." %
                                (', '.join(names[:-1]) + ' and ' + names[-1]))
