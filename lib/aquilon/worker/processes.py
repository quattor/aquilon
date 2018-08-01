# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018  Contributor
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
"""Handling of external processes for the broker happens here.

Most methods will be called as part of a callback chain, and should
expect to handle a generic result from whatever happened earlier in
the chain.

"""
from functools import wraps
import os
import re
import logging
from contextlib import contextmanager
from subprocess import Popen, PIPE
from tempfile import mkdtemp
from threading import Thread, Lock
import types

from six import iteritems

from ipaddress import IPv4Address
from mako.lookup import TemplateLookup
from twisted.python import context
from twisted.python.log import callWithContext, ILogContext
from sqlalchemy.inspection import inspect

from aquilon.exceptions_ import (ProcessException, AquilonError, ArgumentError,
                                 InternalError)
from aquilon.config import Config, running_from_source
from aquilon.aqdb.model import Machine
from aquilon.utils import remove_dir

LOGGER = logging.getLogger(__name__)
config = Config()

DSDB_ENABLED = config.getboolean("dsdb", "enable")
if DSDB_ENABLED:
    try:
        import ms.version
    except ImportError:
        pass
    else:
        # FIXME - this needs to be moved to depends.py after
        # refactoring runtests.py and Config to allow override
        # sys.path for python modules when running tests
        # DSDB python client
        import ms.version
        ms.version.addpkg("requests", "2.7.0")
        ms.version.addpkg("requests-kerberos", "0.5-ms2")
        ms.version.addpkg("kerberos", "1.1.5")
        ms.version.addpkg("dns", "1.10.0")
        ms.version.addpkg('ms.dsdb', '6.0.32')
    import ms.dsdb.client

# subprocess.Popen is not thread-safe in Python 2, so we need locking
_popen_lock = Lock()


class StreamLoggerThread(Thread):
    """Helper class for streaming output as it becomes available."""
    def __init__(self, logger, loglevel, process, stream, filterre=None,
                 context=None):
        self.logger = logger
        self.loglevel = loglevel
        self.process = process
        self.stream = stream
        self.filterre = filterre
        self.context = context
        self.buffer = []
        Thread.__init__(self)

    def run(self):
        while True:
            data = self.stream.readline()
            if data == '' and (self.stream.closed or
                               self.process.returncode is not None):
                break
            if data != '':
                if self.filterre and not self.filterre.search(data):
                    continue
                self.buffer.append(data)

                if self.context:
                    callWithContext(self.context, self.logger.log,
                                    self.loglevel, data.rstrip())
                else:
                    self.logger.log(self.loglevel, data.rstrip())


def run_command(args, env=None, path="/", logger=LOGGER, loglevel=logging.INFO,
                stream_level=None, filterre=None, input=None, timeout_enabled=True):
    '''Run the specified command (args should be a list corresponding to ARGV).

    Returns any output (stdout only).  If the command fails, then
    ProcessException will be raised.  To pass the output back to the client
    pass in a logger and specify loglevel as CLIENT_INFO.

    To reduce the captured output, pass in a compiled regular expression
    with the filterre keyword argument.  Any output lines on stdout will
    only be kept if filterre.search() finds a match.

    All commands are triggered with timeout if timeout_enabled is set to True
    and default_timeout_enabled in config is True or there is timeout value set
    for sepcific tool.
    Timeout can be disabled by passing timeout_enabled=False kwarg to the function
    or in config by stting tool timeout value to 0 or default_timeout_enabled=False.

    '''
    config = Config()
    if env:
        shell_env = env.copy()
    else:
        shell_env = {}

    # Make sure that environment is properly kerberized.
    for envname, envvalue in os.environ.items():
        # AQTEST<something> is used by the testsuite
        if envname.startswith("KRB") or envname.startswith("AQTEST"):
            shell_env[envname] = envvalue

    # Add a default value for the PATH.
    for envname in ["PATH"]:
        if envname not in shell_env and envname in os.environ:
            shell_env[envname] = os.environ[envname]

    # Force any arguments to be strings... takes care of unicode from
    # the database.
    command_args = [str(arg) for arg in args]

    timeout_value = 0
    if timeout_enabled:
        timeout_value = config.lookup_tool_timeout(command_args[0])

    # If the command was not given with an absolute path, then check if there's
    # an override specified in the config file. If not, we'll rely on $PATH.
    if command_args[0][0] != "/":
        command_args[0] = config.lookup_tool(command_args[0])

    if timeout_value:
        command_args = ["/usr/bin/timeout",
                        str(timeout_value)] + \
                       command_args

    simple_command = " ".join(command_args)
    logger.log(loglevel, "run_command: {} (CWD: {})".format(simple_command,
                                                            os.path.abspath(path)))

    if input:
        proc_stdin = PIPE
        logger.info("command `{}` stdin: {}".format(simple_command, input))
    else:
        proc_stdin = None

    # The context contains the log prefix
    ctx = (context.get(ILogContext) or {}).copy()

    with _popen_lock:
        p = Popen(args=command_args, stdin=proc_stdin, stdout=PIPE, stderr=PIPE,
                  cwd=path, env=shell_env)

    # If we want to stream the command's output back to the client while the
    # command is still executing, then we have to doit ourselves. Otherwise,
    # p.communicate() does everything.
    if stream_level is None:
        out, err = p.communicate(input=input)
        if filterre:
            out = "\n".join(line for line in out.splitlines()
                            if filterre.search(line))
    else:
        out_thread = StreamLoggerThread(logger, stream_level, p, p.stdout,
                                        filterre=filterre, context=ctx)
        err_thread = StreamLoggerThread(logger, stream_level, p, p.stderr, context=ctx)
        out_thread.start()
        err_thread.start()
        if proc_stdin:
            p.stdin.write(input)
            p.stdin.close()
        p.wait()
        out_thread.join()
        err_thread.join()

        out = "".join(out_thread.buffer)
        err = "".join(err_thread.buffer)

    if p.returncode >= 0:
        logger.log(loglevel, "command `{}` exited with return code {}".format(simple_command,
                                                                              p.returncode))
        retcode = p.returncode
        signal_num = None
    else:  # pragma: no cover
        logger.log(loglevel, "command `{}` exited with signal {}".format(simple_command,
                                                                         -p.returncode))
        retcode = None
        signal_num = -p.returncode
    if err:
        logger.log(loglevel, "command `{}` stderr: {}".format(simple_command, err))
    if p.returncode == 124:
        raise ProcessException(command=simple_command, out=out, err=err,
                               code=retcode, signalNum=signal_num,
                               filtered=bool(filterre), timeouted=timeout_value)
    elif p.returncode != 0:
        raise ProcessException(command=simple_command, out=out, err=err,
                               code=retcode, signalNum=signal_num,
                               filtered=bool(filterre))
    return out


def run_git(args, env=None, path=".", logger=LOGGER, loglevel=logging.INFO,
            filterre=None, stream_level=None):
    config = Config()
    if env:
        git_env = env.copy()
    else:
        git_env = {}
    git_env["PATH"] = git_env.get("PATH", os.environ.get("PATH", ""))

    for name in ["git_author_name", "git_author_email",
                 "git_committer_name", "git_committer_email"]:
        if not config.has_option("broker", name):
            continue
        value = config.get("broker", name)
        git_env[name.upper()] = value

    if isinstance(args, list):
        git_args = args[:]
        if git_args[0] != "git":
            git_args.insert(0, "git")
    else:
        git_args = ["git", args]

    return run_command(git_args, env=git_env, path=path, logger=logger,
                       loglevel=loglevel, filterre=filterre,
                       stream_level=stream_level)


def cache_version(config, logger=LOGGER):
    """Try to determine the broker version by examining the path
    to this source file.  If this file path matches
    /aquilon/PROJ/aqd/<version>/ (likely /ms/dist) or
    /aquilon/aqd/<version>/ (likely /ms/dev) then use <version>.

    Otherwise, run git describe to get the most recent tag.

    """

    if config.has_option("broker", "version"):
        return

    version_re = re.compile(r'/aquilon(?:/PROJ)?/aqd/([^/]+)/')
    m = version_re.search(__file__)
    if m and m.group(1) != "lib" and m.group(1) != "bin":
        config.set("broker", "version", m.group(1))
        return

    try:
        out = run_git("describe", logger=logger,
                      path=config.get("broker", "srcdir"))
        config.set("broker", "version", out.strip())
    except ProcessException as e:
        logger.info("Could not run git describe to get version: %s", e)
        config.set("broker", "version", "Unknown")


class GitRepo(object):
    """
    Git repository wrapper

    This class is not meant to be a simple wrapper around git, but rather to
    implement higher level functions - even if some of those functions can be
    translated to a single git command.
    """

    def __init__(self, path, logger, loglevel=logging.INFO):
        self.path = path
        self.logger = logger
        self.loglevel = loglevel

    @staticmethod
    def template_king(logger, loglevel=logging.INFO):
        """
        Constructor for template-king
        """

        config = Config()
        return GitRepo(config.get("broker", "kingdir"), logger=logger,
                       loglevel=loglevel)

    @staticmethod
    def domain(domain, logger, loglevel=logging.INFO):
        """
        Constructor for domains
        """

        config = Config()
        domainsdir = config.get('broker', 'domainsdir')
        return GitRepo(os.path.join(domainsdir, domain), logger=logger,
                       loglevel=loglevel)

    def run(self, args, filterre=None, stream_level=None):
        return run_git(args, path=self.path, logger=self.logger,
                       loglevel=self.loglevel, filterre=filterre,
                       stream_level=stream_level)

    def ref_contains_commit(self, commit_id, ref='HEAD'):
        """
        Check if a given reference (by default, HEAD) contains a given commit ID
        """

        filterre = re.compile('^' + commit_id + '$')
        try:
            found = self.run(['rev-list', ref], filterre=filterre)
        except ProcessException as pe:
            if pe.code != 128:
                raise
            else:
                found = None

        return found

    def ref_commit(self, ref='HEAD', compel=True):
        """
        Return the top commit of a ref, by default HEAD
        """
        try:
            commit = self.run(['rev-parse', '--verify', '-q', ref + '^{commit}'])
            return commit.strip()
        except ProcessException as pe:
            if pe.code == 1:
                if compel:
                    raise ArgumentError("Ref %s could not be translated to an "
                                        "existing commit ID." % ref)
                return None
            raise

    def ref_tree(self, ref='HEAD', compel=True):
        """
        Return the tree ID a ref (by default, HEAD) points to
        """
        try:
            tree = self.run(['rev-parse', '--verify', '-q', ref + '^{tree}'])
            return tree.strip()
        except ProcessException as pe:
            if pe.code == 1:
                if compel:
                    raise ArgumentError("Ref %s not found.", ref)
                return None
            raise

    @contextmanager
    def temp_clone(self, branch):
        """
        Create a temporary clone for working on the given branch

        This function is a context manager meant to be used in a with statement.
        The temporary clone is removed automatically.
        """
        config = Config()
        # TODO: is rundir suitable for this purpose?
        rundir = config.get("broker", "rundir")
        tempdir = mkdtemp(prefix="git_clone_", dir=rundir)
        try:
            run_git(["clone", "--shared", "--branch", branch, "--",
                     self.path, branch],
                    path=tempdir, logger=self.logger, loglevel=self.loglevel)
            yield GitRepo(os.path.join(tempdir, branch), logger=self.logger,
                          loglevel=self.loglevel)
        finally:
            remove_dir(tempdir, logger=self.logger)

    def push_origin(self, ref, force=False):
        """
        Push a ref to the origin remote
        """
        if force:
            self.run(["push", "--force", "origin", ref])
        else:
            self.run(["push", "origin", ref])


IP_NOT_DEFINED_RE = re.compile(r"Host with IP address "
                               r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"
                               r" is not defined")

BUILDING_NOT_FOUND = re.compile(r"bldg [a-zA-Z0-9]{2} doesn't exists")

CAMPUS_NOT_FOUND = re.compile(r"campus [a-zA-Z0-9]{2} doesn't exist")

DNS_DOMAIN_NOT_FOUND = re.compile(r"DNS domain ([-\w\.\d]+) doesn't exists")

DNS_DOMAIN_EXISTS = re.compile(r"DNS domain [-\w\.\d]+ already defined")

# The regexp is taken from DSDB
INVALID_NAME_RE = re.compile(r"[^A-Za-z0-9_.-]")


def dsdb_enabled(view_func):
    def _decorator(request, *args, **kwargs):
        if DSDB_ENABLED:
            response = view_func(request, *args, **kwargs)
            return response
        return
    return wraps(view_func)(_decorator)


class DSDBEnabledMeta(type):
    def __new__(mcls, name, bases, body):
        for name, obj in body.items():
            if name[:2] == name[-2:] == '__' or name in ['normalize_iface', 'getenv']:
                # skip special method names like __init__ and helper class methods
                continue
            if isinstance(obj, types.FunctionType):
                # decorate all functions
                # class variables, classmethods and staticmethods are not decorated
                body[name] = dsdb_enabled(obj)
        return super(DSDBEnabledMeta, mcls).__new__(mcls, name, bases, body)

    def __call__(cls, *args, **kwargs):
        # create a new instance for this class
        # add in `dsdbclient` attribute
        instance = super(DSDBEnabledMeta, cls).__call__(*args, **kwargs)
        if DSDB_ENABLED:
            if instance.dsdb_use_testdb:
                os.environ['DSDB_USE_TESTDB'] = "1"

            # a timeout of zero in the broker config means "no timeout";  for ms.dsdb,
            # zero means immediate timeout (i.e. non-blocking operation).
            use_timeout = config.lookup_tool_timeout('dsdb') or None

            instance.dsdbclient = ms.dsdb.client.DSDB(plant='prod',
                                                      timeout=use_timeout)
        return instance


class DSDBRunner(object):
    __metaclass__ = DSDBEnabledMeta
    snapshot_handlers = {}

    def __init__(self, logger=LOGGER):
        self.logger = logger
        self.dsdb_use_testdb = config.getboolean("dsdb", "dsdb_use_testdb")
        self.actions = []
        self.rollback_list = []

    def normalize_iface(self, iface):
        return INVALID_NAME_RE.sub("_", iface)

    def snapshot(self, obj):
        env_calculate_method = self.snapshot_handlers.get(inspect(obj.__class__).polymorphic_identity)
        return env_calculate_method(self, obj)

    def commit(self, verbose=False):
        for cmd_line, args, rollback, error_filter, ignore_msg in self.actions:
            try:
                if cmd_line:
                    cmd = ["dsdb"]
                    cmd.extend(args)
                    if verbose:
                        self.logger.client_info("DSDB: %s" %
                                                " ".join(str(a) for a in args))
                    run_command(cmd, env=self.getenv(), logger=self.logger)
                else:
                    self.invoke_dsdb_module(args, verbose=verbose)
            except ProcessException as err:
                if error_filter and err.out and error_filter.search(err.out):
                    self.logger.warning(ignore_msg)
                else:
                    raise
            except Exception as err:
                self.logger.warning(str(err))
                if error_filter:
                    self.logger.warning(ignore_msg)
                else:
                    raise AquilonError("DSDB command failed: {}.".format(', '.join(args.keys())))
            if rollback:
                self.rollback_list.append((cmd_line, rollback))

    def rollback(self, verbose=False):
        self.rollback_list.reverse()
        rollback_failures = []
        for cmd_line, args in self.rollback_list:
            try:
                if cmd_line:
                    cmd = ["dsdb"]
                    cmd.extend(args)
                    self.logger.client_info("DSDB: %s" %
                                            " ".join(str(a) for a in args))
                    run_command(cmd, env=self.getenv(), logger=self.logger)
                else:
                    self.invoke_dsdb_module(args, verbose=True)
            except Exception as err:
                rollback_failures.append(str(err))

        did_something = bool(self.rollback_list)
        del self.rollback_list[:]

        if rollback_failures:
            raise AquilonError("DSDB rollback failed, DSDB state is "
                               "inconsistent: " + "\n".join(rollback_failures))
        elif did_something:
            self.logger.client_info("DSDB rollback completed.")

    def invoke_dsdb_module(self, args, verbose=False):
        for method, attributes in args.iteritems():
            if verbose:
                self.logger.client_info("DSDB: command {} "
                                        "called with arguments: {}.".format(method,
                                                                            attributes))
            dsdb_client_action = getattr(self.dsdbclient, method)
            dsdb_client_action(**attributes)

    def commit_or_rollback(self, error_msg=None, verbose=False):
        try:
            self.commit(verbose=verbose)
        except Exception as err:
            if not error_msg:
                error_msg = "DSDB update failed"
            self.logger.warning(str(err))
            self.rollback(verbose=verbose)
            raise ArgumentError(error_msg)

    def add_action(self, command_args, rollback_args, error_filter=None,
                   ignore_msg=False, cmd_line=True):
        """
        Register an action to execute and it's rollback counterpart.

        command_args: the DSDB command to execute
        rollback_args: the DSDB command to execute on rollback
        error_filter: regexp of error messages in the output of dsdb that
                      should be ignored
        ignore_msg: message to log if the error_filter matched
        """
        if error_filter and not ignore_msg:
            raise InternalError("Specifying an error filter needs the message "
                                "specified as well.")
        self.actions.append((cmd_line, command_args, rollback_args, error_filter,
                             ignore_msg))

    def getenv(self):
        if self.dsdb_use_testdb:
            return {"DSDB_USE_TESTDB": "true"}
        return None

    def add_campus(self, campus, comments):
        command = ["add_campus_aq", "-campus_name", campus]
        if comments:
            command.extend(["-comments", comments])
        rollback = ["delete_campus_aq", "-campus", campus]
        self.add_action(command, rollback)

    def del_campus(self, campus):
        command = ["delete_campus_aq", "-campus", campus]
        rollback = ["add_campus_aq", "-campus_name", campus]
        self.add_action(command, rollback, CAMPUS_NOT_FOUND,
                        "DSDB does not have campus %s defined, proceeding.")

    def add_city(self, city, country, fullname):
        command = ["add_city_aq", "-city_symbol", city, "-country_symbol",
                   country, "-city_name", fullname]
        rollback = ["delete_city_aq", "-city", city]
        self.add_action(command, rollback)

    def update_city(self, city, campus, prev_campus):
        command = ["update_city_aq", "-city", city, "-campus", campus]
        # We can't revert to an empty campus
        if prev_campus:
            rollback = ["update_city_aq", "-city", city, "-campus", prev_campus]
        else:
            rollback = None
        self.add_action(command, rollback)

    def del_city(self, city, old_country, old_fullname):
        command = ["delete_city_aq", "-city", city]
        rollback = ["add_city_aq", "-city_symbol", city, "-country_symbol",
                    old_country, "-city_name", old_fullname]
        self.add_action(command, rollback)

    def add_campus_building(self, campus, building):
        command = ["add_campus_building_aq", "-campus_name", campus,
                   "-building_name", building]
        rollback = ["delete_campus_building_aq", "-campus_name", campus,
                    "-building_name", building]
        self.add_action(command, rollback)

    def add_building(self, building, city, building_addr):
        command = ["add_building_aq", "-building_name", building, "-city", city,
                   "-building_addr", building_addr]
        rollback = ["delete_building_aq", "-building", building]
        self.add_action(command, rollback)

    def del_campus_building(self, campus, building):
        command = ["delete_campus_building_aq", "-campus_name", campus,
                   "-building_name", building]
        rollback = ["add_campus_building_aq", "-campus_name", campus,
                    "-building_name", building]
        self.add_action(command, rollback)

    def del_building(self, building, old_city, old_addr):
        command = ["delete_building_aq", "-building", building]
        rollback = ["add_building_aq", "-building_name", building,
                    "-city", old_city, "-building_addr", old_addr]
        self.add_action(command, rollback, BUILDING_NOT_FOUND,
                        "DSDB does not have building %s defined, "
                        "proceeding." % building)

    def update_building(self, building, address, old_addr):
        command = ["update_building_aq", "-building_name", building,
                   "-building_addr", address]
        rollback = ["update_building_aq", "-building_name", building,
                    "-building_addr", old_addr]
        self.add_action(command, rollback)

    def snapshot_rack(self, dbrack):
        snapshot_rack = {'floor': dbrack.room.floor if dbrack.room else '0',
                         'comp_room': dbrack.room.name if dbrack.room else 'unknown',
                         'row': dbrack.rack_row,
                         'column': dbrack.rack_column,
                         'comments': dbrack.comments}
        return snapshot_rack

    def snapshot_chassis(self, dbchassis):
        snapshot_chassis = {'comments': dbchassis.comments}
        return snapshot_chassis

    def add_rack(self, dbrack):
        dsdb_client_command_dict = {'add_rack': {'id': dbrack.name.replace(dbrack.building.name, ''),
                                                 'building': dbrack.building.name,
                                                 'floor': dbrack.room.floor if dbrack.room else '0',
                                                 'comp_room': dbrack.room.name if dbrack.room else 'unknown',
                                                 'row': dbrack.rack_row,
                                                 'column': dbrack.rack_column,
                                                 'comments': dbrack.comments}}
        dsdb_client_rollback_dict = {'delete_rack': {'rack_name': dbrack.name}}
        self.add_action(dsdb_client_command_dict, dsdb_client_rollback_dict, cmd_line=False)

    def update_rack(self, dbrack, snapshot_rack):
        dsdb_client_command_dict = {'update_rack': {'rack': dbrack.name,
                                                 'floor': dbrack.room.floor if dbrack.room else '0',
                                                 'comp_room': dbrack.room.name if dbrack.room else 'unknown',
                                                 'row': dbrack.rack_row,
                                                 'column': dbrack.rack_column,
                                                 'comments': dbrack.comments}}
        dsdb_client_rollback_dict = {'update_rack': {'rack': dbrack.name,
                                                     'floor': snapshot_rack['floor'],
                                                     'comp_room': snapshot_rack['comp_room'],
                                                     'row': snapshot_rack['row'],
                                                     'column': snapshot_rack['column'],
                                                     'comments': snapshot_rack['comments']}}
        # Ignoring DSDB failures for updates now, as many racks do not exist in DSDB
        self.add_action(dsdb_client_command_dict, dsdb_client_rollback_dict, cmd_line=False,
                        error_filter=True, ignore_msg="Update rack {} in DSDB failed, "
                                                      "proceeding in AQDB.".format(dbrack.name))

    def del_rack(self, dbrack):
        dsdb_client_command_dict = {'delete_rack': {'rack_name': dbrack.name}}
        dsdb_client_rollback_dict = {'add_rack': {'id': dbrack.name.replace(dbrack.building.name, ''),
                                                  'building': dbrack.building.name,
                                                  'floor': dbrack.room.floor if dbrack.room else '0',
                                                  'comp_room': dbrack.room.name if dbrack.room else 'unknown',
                                                  'row': dbrack.rack_row,
                                                  'column': dbrack.rack_column,
                                                  'comments': dbrack.comments}}
        # Ignoring DSDB failures for updates now, as many racks do not exist in DSDB
        self.add_action(dsdb_client_command_dict, dsdb_client_rollback_dict, cmd_line=False, error_filter=True,
                        ignore_msg="Delete rack {} in DSDB failed, proceeding in AQDB.".format(dbrack.name))

    def add_chassis(self, dbchassis):
        dsdb_client_command_dict = {'add_chassis': {'id': dbchassis.label.replace(dbchassis.location.rack.name + 'c', ''),
                                                    'rack': dbchassis.location.rack.name,
                                                    'comments': dbchassis.comments}}
        dsdb_client_rollback_dict = {'delete_chassis': {'chassis_name': dbchassis.label}}
        self.add_action(dsdb_client_command_dict, dsdb_client_rollback_dict, cmd_line=False)

    def update_chassis(self, dbchassis, snapshot_chassis):
        if dbchassis.comments:
            dsdb_client_command_dict = {'update_chassis': {'chassis': dbchassis.label,
                                                           'comments': dbchassis.comments}}
            dsdb_client_rollback_dict = {'update_chassis': {'chassis': dbchassis.label,
                                                            'comments': snapshot_chassis['comments']}}
            # Ignoring DSDB failures for updates now, as many chassis do not exist in DSDB
            self.add_action(dsdb_client_command_dict, dsdb_client_rollback_dict, cmd_line=False,
                            error_filter=True, ignore_msg="Update chassis {} in DSDB failed, "
                                                          "proceeding in AQDB.".format(dbchassis.label))

    def delete_chassis(self, dbchassis):
        dsdb_client_command_dict = {'delete_chassis': {'chassis_name': dbchassis.label}}
        dsdb_client_rollback_dict = {'add_chassis': {'id': dbchassis.label.replace(dbchassis.location.rack.name + 'c', ''),
                                                     'rack': dbchassis.location.rack.name,
                                                     'comments': dbchassis.comments}}
        # Ignoring DSDB failures for updates now, as many racks do not exist in DSDB
        self.add_action(dsdb_client_command_dict, dsdb_client_rollback_dict, cmd_line=False, error_filter=True,
                        ignore_msg="Delete chassis {} in DSDB failed, proceeding in AQDB.".format(dbchassis.label))

    def add_host_details(self, fqdn, ip, iface=None, mac=None, primary=None,
                         comments=None, **_):
        if not isinstance(ip, IPv4Address):
            return

        command = ["add_host", "-host_name", fqdn,
                   "-ip_address", ip, "-status", "aq"]
        if iface:
            command.extend(["-interface_name", self.normalize_iface(iface)])
        if mac:
            command.extend(["-ethernet_address", mac])
        if primary and str(primary) != str(fqdn):
            command.extend(["-primary_host_name", primary])
        if comments:
            command.extend(["-comments", comments])

        rollback = ["delete_host", "-ip_address", ip]
        self.add_action(command, rollback)

    def update_host_details(self, fqdn, iface=None, new_ip=None, new_mac=None,
                            new_comments=None, old_ip=None, old_mac=None,
                            old_comments=None, **_):
        command = ["update_aqd_host", "-host_name", fqdn]
        if iface:
            iface = self.normalize_iface(iface)
            command.extend(["-interface_name", iface])

        rollback = command[:]

        if new_ip and new_ip != old_ip and isinstance(new_ip, IPv4Address):
            command.extend(["-ip_address", new_ip])
            rollback.extend(["-ip_address", old_ip])
        if new_mac and new_mac != old_mac:
            command.extend(["-ethernet_address", new_mac])
            rollback.extend(["-ethernet_address", old_mac])
        if new_comments != old_comments:
            command.extend(["-comments", new_comments or ""])
            rollback.extend(["-comments", old_comments or ""])

        self.add_action(command, rollback)

    def update_host_iface_name(self, old_fqdn, new_fqdn,
                               old_iface, new_iface, **_):
        old_iface = self.normalize_iface(old_iface)
        new_iface = self.normalize_iface(new_iface)
        command = ["update_aqd_host", "-host_name", old_fqdn]
        rollback = ["update_aqd_host", "-host_name", new_fqdn]

        if old_fqdn != new_fqdn:
            command.extend(["-new_host_name", new_fqdn])
            rollback.extend(["-new_host_name", old_fqdn])
        if old_iface and old_iface != new_iface:
            command.extend(["-interface_name", old_iface,
                            "-new_interface_name", new_iface])
            rollback.extend(["-interface_name", new_iface,
                             "-new_interface_name", old_iface])

        self.add_action(command, rollback)

    def delete_host_details(self, fqdn, ip, iface=None, mac=None, primary=None,
                            comments=None, **_):
        if not isinstance(ip, IPv4Address):
            return
        command = ["delete_host", "-ip_address", ip]
        rollback = ["add_host", "-host_name", fqdn,
                    "-ip_address", ip, "-status", "aq"]
        if iface:
            rollback.extend(["-interface_name", self.normalize_iface(iface)])
        if mac:
            rollback.extend(["-ethernet_address", mac])
        if primary and str(primary) != str(fqdn):
            rollback.extend(["-primary_host_name", primary])
        if comments:
            rollback.extend(["-comments", comments])

        self.add_action(command, rollback, IP_NOT_DEFINED_RE,
                        "DSDB did not have a host with this IP address, "
                        "proceeding.")

    @classmethod
    def snapshot_hw(cls, dbhw_ent):
        """
        Make a snapshot of the interface parameters.

        update_host() will use this snapshot to decide what has changed and
        what DSDB commands have to be executed.

        Comment handling is a bit complicated, because we have more ways to
        store comments in Aquilon than in DSDB. The rules are:

        - If the interface has a comment, use that.

        - Otherwise take the comment from the hardware entity.

          Exception: management interfaces
        """

        real_primary = dbhw_ent.fqdn
        hwdata = {"by-ip": {},
                  "by-fqdn": {},
                  "primary": real_primary}

        # For each of the addresses held by this hardware_entity we need to
        # create an entry in DSDB.  The following loop makes a snapshot of
        # expected state of the information in DSDB.
        for addr in dbhw_ent.all_addresses():
            # Do not propagate to DSDB if the network is not internal,
            # there are no FQDN's associated with this address, or
            # the address is shared with other devices.
            if not addr.network.is_internal:
                continue
            if not addr.fqdns:
                continue
            if addr.is_shared:
                continue
            if not isinstance(addr.ip, IPv4Address):
                continue

            # In AQDB there may be multiple domain names associated with
            # an address, in DSDB there can only be one.  Thus we pick
            # the first address to propagate.
            dns_record = addr.dns_records[0]

            # By default we take the comments from the hardware_entity,
            # if an interface comment exists then this will be taken
            # in preference.  Management interfaces are added as stand-alone
            # entries, therefore we do not take the hardware_entity comment
            # but allow the following code to take it from the interface.
            if addr.interface.interface_type != 'management':
                comments = dbhw_ent.comments
            else:
                comments = None

            iface = addr.logical_name
            if addr.interface.comments and not \
                    addr.interface.comments.startswith("Created automatically"):
                comments = addr.interface.comments

            # Determine if we need to specify a primary name to DSDB.  By
            # doing so we are associating this record with another.
            # Note, the existence of a primary hostname affects the order
            # that entriers are processed in update_host()
            if addr.interface.interface_type == "management":
                # Do not use -primary_host_name for the management address
                # as we do not wish to associate them with the host currently
                # on the machine (which may change).
                primary = None
            elif str(dns_record.fqdn) == real_primary:
                # Avoid circular dependency - do not set the 'primary' key for
                # the real primary name
                primary = None
            elif not isinstance(dbhw_ent, Machine):
                # Not a machine - we don't care about srvloc
                primary = real_primary
            elif dns_record.reverse_ptr and str(dns_record.reverse_ptr.fqdn) == real_primary:
                # If the reverse PTR record points to the primary name in AQDB,
                # then pass the -primary_name flag to DSDB
                primary = real_primary
            else:
                # Avoid using -primary_name, to please srvloc
                primary = None

            # Exclude the MAC address for aliases
            if addr.label:
                mac = None
            else:
                mac = addr.interface.mac

            ifdata = {'iface': iface,
                      'ip': addr.ip,
                      'mac': mac,
                      'fqdn': str(dns_record.fqdn),
                      'primary': primary,
                      'comments': comments}

            hwdata["by-ip"][ifdata["ip"]] = ifdata
            hwdata["by-fqdn"][ifdata["fqdn"]] = ifdata

        # The primary address of Zebra hosts needs extra care. Here, we cheat a
        # bit - we do not check if the primary name is a service address, but
        # instead check if it has an IP address and it was not handled above.
        if (dbhw_ent.primary_ip and
                    str(dbhw_ent.primary_name.fqdn) not in hwdata["by-fqdn"]):
            ifdata = {'iface': "vip",
                      'ip': dbhw_ent.primary_ip,
                      'mac': None,
                      'fqdn': str(dbhw_ent.primary_name),
                      'primary': None,
                      'comments': None}

            hwdata["by-ip"][ifdata["ip"]] = ifdata
            hwdata["by-fqdn"][ifdata["fqdn"]] = ifdata

        return hwdata

    def update_host(self, dbhw_ent, old_hwdata):
        """Update a dsdb host entry.

        The calling code (the aq update_interface command) treats the
        hostname and interface name (except for zebra hosts!) as unchanging .
        There is an update_host dsdb command that lets the mac address,
        ip address (and comments, if we kept them) change.

        Any other changes have to be done by removing the old DSDB
        entry and adding a new one.

        Please note that in case of zebra interfaces adding a new ip address
        to the same interface may result in adding/removing DSDB entries.
        """
        if dbhw_ent:
            new_hwdata = self.snapshot_hw(dbhw_ent)
        else:
            new_hwdata = {"by-ip": {},
                          "by-fqdn": {},
                          "primary": None}

        if not old_hwdata:
            old_hwdata = {"by-ip": {},
                          "by-fqdn": {},
                          "primary": None}

        deletes = []
        adds = []
        # Host/interface names cannot be updated simultaneously with IP/MAC
        # addresses or comments
        addr_updates = []
        name_updates = []

        # Run through all of the entries in the old snapshot and attempt
        # to match them to their corrisponding new entry.
        for fqdn, old_ifdata in old_hwdata["by-fqdn"].items():
            # Locate the new information about this address by either
            # its FQDN or IP address.
            if fqdn in new_hwdata["by-fqdn"]:
                new_ifdata = new_hwdata["by-fqdn"][fqdn]
            elif old_ifdata["ip"] in new_hwdata["by-ip"]:
                new_ifdata = new_hwdata["by-ip"][old_ifdata["ip"]]
            else:
                new_ifdata = None

            # If either the old or the new entry is bound to a primary name but
            # the other is not, then we have to delete & re-add it.  Note this
            # will be re-added in the following loop as we did not delete the
            # entry from new_hwdata.
            if new_ifdata and bool(old_ifdata["primary"]) != bool(new_ifdata["primary"]):
                new_ifdata = None

            # If there is no new data then record a delete (note above).
            if not new_ifdata:
                deletes.append(old_ifdata)
                continue

            # Create a dict with entries in old_ifdata prefiexd with 'old_'
            # and entries in new_ifdata prefixed with 'new_'
            kwargs = {p + k: v
                      for (p, d) in [('old_', old_ifdata),
                                     ('new_', new_ifdata)]
                      for k, v in iteritems(d)}

            if (old_ifdata['ip'] != new_ifdata['ip'] or
                        old_ifdata['mac'] != new_ifdata['mac'] or
                        old_ifdata['comments'] != new_ifdata['comments']):
                addr_updates.append(kwargs)

            if (old_ifdata['fqdn'] != new_ifdata['fqdn'] or
                        old_ifdata['iface'] != new_ifdata['iface']):
                name_updates.append(kwargs)

            # Delete the entries from new_hwdata.  We have recorded an
            # update.  The contents of new_hwdata is used in the following
            # loop to record additions.
            del new_hwdata["by-fqdn"][new_ifdata["fqdn"]]
            del new_hwdata["by-ip"][new_ifdata["ip"]]

        # For all of the recoreds remaining in new_hwdata (see above)
        # record an addtion opperation.
        adds = new_hwdata["by-fqdn"].values()

        # Add the primary address first, and delete it last. The primary address
        # is identified by having an empty ['primary'] key (this is true for the
        # management address as well, but that does not matter).
        sort_by_primary = lambda x: x['primary'] or ""
        adds.sort(key=sort_by_primary)
        deletes.sort(key=sort_by_primary, reverse=True)

        for attrs in deletes:
            self.delete_host_details(**attrs)

        for kwargs in addr_updates:
            # The old FQDN and interface name are the fixed point
            self.update_host_details(fqdn=kwargs['old_fqdn'],
                                     iface=kwargs['old_iface'],
                                     **kwargs)

        for kwargs in name_updates:
            self.update_host_iface_name(**kwargs)

        for attrs in adds:
            self.add_host_details(**attrs)

    def add_dns_domain(self, dns_domain, comments):
        if not comments:
            # DSDB requires the comments field, even if it is empty
            comments = ""
        command = ["add_dns_domain", "-domain_name", dns_domain,
                   "-comments", comments]
        rollback = ["delete_dns_domain", "-domain_name", dns_domain]
        self.add_action(command, rollback, DNS_DOMAIN_EXISTS,
                        "The DNS domain %s already exists in DSDB, "
                        "proceeding." % dns_domain)

    def delete_dns_domain(self, dns_domain, old_comments):
        command = ["delete_dns_domain", "-domain_name", dns_domain]
        rollback = ["add_dns_domain", "-domain_name", dns_domain,
                    "-comments", old_comments]
        self.add_action(command, rollback, DNS_DOMAIN_NOT_FOUND,
                        "The DNS domain %s does not exist in DSDB, "
                        "proceeding." % dns_domain)

    def show_rack(self, rackname):
        rack_data = self.dsdbclient.show_rack(rack_name=rackname).results()
        fields = {}
        if len(rack_data) > 1:
            raise ValueError("Multiple racks with the same name {} "
                             "prefix found.".format(rackname))
        if rack_data:
            fields = {"rack_row": rack_data[0]["row"],
                      "rack_col": rack_data[0]["column"]}

        if not fields or not fields["rack_row"] or not fields["rack_col"]:
            raise ValueError("Rack {} is not found in DSDB or missing "
                             "row and/or col data.".format(rackname))
        return fields

    def show_host(self, hostname):
        (short, dot, dns_domain) = hostname.partition(".")
        fields = {}
        if not dot:
            fields["fqdn"] = short + ".ms.com"
            fields["dsdb_lookup"] = short
        elif not dns_domain:
            fields["fqdn"] = short + "ms.com"
            fields["dsdb_lookup"] = short
        elif dns_domain != "ms.com":
            fields["fqdn"] = hostname
            fields["dsdb_lookup"] = hostname
        else:
            fields["fqdn"] = hostname
            fields["dsdb_lookup"] = short

        host_data = self.dsdbclient.show_host(host_name=fields["dsdb_lookup"]).results()
        if len(host_data) > 1:
            raise ValueError("Multiple hosts with same name {} "
                             "prefix found in DSDB".format(fields["dsdb_lookup"]))
        if host_data:
            fields["primary_name"] = host_data[0].get("primary_hostname")
            fields["node"] = host_data[0].get("nodename")
            fields["dns"] = host_data[0].get("DNS_domain")
            fields["state"] = host_data[0].get("state")
        else:
            raise ValueError("Host {} is not found in DSDB or "
                             "multiple hosts with same name prefix found in DSDB".format(fields["dsdb_lookup"]))
        return fields

    def add_alias(self, alias, target, comments):
        command = ["add_host_alias", "-host_name", target,
                   "-alias_name", alias]
        if comments:
            command.extend(["-comments", comments])
        rollback = ["delete_host_alias", "-alias_name", alias]
        self.add_action(command, rollback)

    def del_alias(self, alias, old_target, old_comments):
        command = ["delete_host_alias", "-alias_name", alias]
        rollback = ["add_host_alias", "-host_name", old_target,
                    "-alias_name", alias]
        if old_comments:
            rollback.extend(["-comments", old_comments])
        self.add_action(command, rollback)

    def update_alias(self, alias, target, comments, old_target, old_comments):
        command = ["update_host_alias", "-alias", alias,
                   "-new_host", target]
        rollback = ["update_host_alias", "-alias", alias,
                    "-new_host", old_target]
        if comments != old_comments:
            command.extend(["-new_comments", comments or ""])
            rollback.extend(["-new_comments", old_comments or ""])
        self.add_action(command, rollback)


def build_mako_lookup(config, kind, **kwargs):
    # This duplicates the logic from lookup_file_path(), but we don't want to
    # move the mako dependency to aquilon.config
    srcdir = config.get("broker", "srcdir")
    srcpath = os.path.join(srcdir, "etc", "mako", kind)

    directories = []
    if running_from_source():
        # If we're running from the source, then ignore any installed files
        directories.append(srcpath)
    else:
        directories.append(os.path.join("/etc", "aquilon", "mako", kind))
        directories.append(os.path.join("/usr", "share", "aquilon", "mako", kind))
        if os.path.exists(srcpath):
            directories.append(srcpath)

    return TemplateLookup(directories=directories, **kwargs)


DSDBRunner.snapshot_handlers['rack'] = DSDBRunner.snapshot_rack
DSDBRunner.snapshot_handlers['chassis'] = DSDBRunner.snapshot_chassis
