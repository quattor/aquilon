# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
    Useful subroutines that don't fit in any place to particularly for aquilon.
"""

import errno
import gzip
import json
import logging
import os
import re
import signal
from cStringIO import StringIO
from tempfile import mkstemp

from ipaddr import IPv4Address, AddressValueError

from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.config import Config

LOGGER = logging.getLogger(__name__)

ratio_re = re.compile('^\s*(?P<left>\d+)\s*(?:[:/]\s*(?P<right>\d+))?\s*$')
yes_re = re.compile("^(true|yes|y|1|on|enabled)$", re.I)
no_re = re.compile("^(false|no|n|0|off|disabled)$", re.I)
_unpadded_re = re.compile(r'\b([0-9a-f])\b')
_nocolons_re = re.compile(r'^([0-9a-f]{2}){6}$')
_two_re = re.compile(r'[0-9a-f]{2}')
_padded_re = re.compile(r'^([0-9a-f]{2}:){5}([0-9a-f]{2})$')

def kill_from_pid_file(pid_file):  # pragma: no cover
    if os.path.isfile(pid_file):
        f = open(pid_file)
        p = f.read()
        f.close()
        pid = int(p)
        print 'Killing pid %s' % pid
        try:
            os.kill(pid, signal.SIGQUIT)
        except OSError, err:
            print 'Failed to kill %s: %s' % (pid, err.strerror)


def monkeypatch(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator


def confirm(prompt=None, resp=False):  # pragma: no cover
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [y]|n:
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y:
    False
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: y
    True

    """

    if prompt is None:
        prompt = 'Confirm'

    if resp:
        prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
    else:
        prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')

    while True:
        ans = raw_input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'yes', 'n', 'N', 'no']:
            print 'please enter y or n.'
            continue
        if ans == 'y' or ans == 'Y' or ans == 'yes':
            return True
        if ans == 'n' or ans == 'N' or ans == 'no':
            return False


def force_ipv4(label, value):
    if value is None:
        return None
    if isinstance(value, IPv4Address):
        return value
    try:
        return IPv4Address(value)
    except AddressValueError, e:
        raise ArgumentError("Expected an IPv4 address for %s: %s" % (label, e))


def force_int(label, value):
    """Utility method to force incoming values to int and wrap errors."""
    if value is None:
        return None
    try:
        result = int(value)
    except ValueError:
        raise ArgumentError("Expected an integer for %s." % label)
    return result


def force_float(label, value):
    """Utility method to force incoming values to float and wrap errors."""
    if value is None:
        return None
    try:
        result = float(value)
    except ValueError:
        raise ArgumentError("Expected an floating point number for %s." % label)
    return result


def force_ratio(label, value):
    """Utility method to force incoming values to int ratio and wrap errors."""
    if value is None:
        return (None, None)
    m = ratio_re.search(value)
    if not m:
        raise ArgumentError("Expected a ratio like 1:2 for %s but got '%s'" %
                            (label, value))
    (left, right) = m.groups()
    if right is None:
        right = 1
    return (int(left), int(right))


def force_boolean(label, value):
    """Utility method to force incoming values to boolean and wrap errors."""
    if value is None:
        return None
    if yes_re.match(value):
        return True
    if no_re.match(value):
        return False
    raise ArgumentError("Expected a boolean value for %s." % label)


def force_mac(label, value):
    # Allow nullable Mac Addresses, consistent with behavior of IPV4
    if value is None:
        return None

    # Strip, lower, and then use a regex for zero-padding if needed...
    value = _unpadded_re.sub(r'0\1', str(value).strip().lower())
    # If we have exactly twelve hex characters, add the colons.
    if _nocolons_re.search(value):
        value = ":".join(_two_re.findall(value))
    # Check to make sure we're good.
    if _padded_re.search(value):
        return value
    raise ArgumentError("Expected a MAC address like 00:1a:2b:3c:0d:55, "
                        "001a2b3c0d55 or 0:1a:2b:3c:d:55 for %s." % label)


def force_ascii(label, value):
    if value is None:
        return None
    try:
        value = value.decode('ascii')
    except UnicodeDecodeError:
        raise ArgumentError("Only ASCII characters are allowed for %s." % label)
    return value


def force_list(label, value):
    """
    Convert a value containing embedded newlines to a list.

    The function also removes empty lines and lines starting with '#'.
    """
    if value is None:
        return None
    lines = map(lambda x: force_ascii('line', x.strip()), value.splitlines())
    return filter(lambda x: x and not x.startswith("#"), lines)


def force_json_dict(label, value):
    if value is None:
        return None
    try:
        value = json.loads(value)
    except ValueError, e:
        raise ArgumentError("The json string specified for %s is invalid : %s"
                            % (label, e))
    return value


def first_of(iterable, function):
    """
    Return the first matching element of an iterable

    This function is useful if you already know there is at most one matching
    element.
    """
    for item in iterable:
        if function(item):
            return item
    return None

def remove_dir(dir, logger=LOGGER):
    """Remove a directory.  Could have been implemented as a call to rm -rf."""
    for root, dirs, files in os.walk(dir, topdown=False):
        for name in files:
            try:
                thisfile = os.path.join(root, name)
                os.remove(thisfile)
            except OSError, e:
                logger.info("Failed to remove '%s': %s" % (thisfile, e))
        for name in dirs:
            try:
                thisdir = os.path.join(root, name)
                os.rmdir(thisdir)
            except OSError, e:
                # If this 'directory' is a symlink, the rmdir command
                # will fail.  Try to remove it as a file.  If this
                # fails, report the original error.
                try:
                    os.remove(thisdir)
                except OSError, e1:
                    logger.info("Failed to remove '%s': %s" % (thisdir, e))
    try:
        os.rmdir(dir)
    except OSError, e:
        logger.info("Failed to remove '%s': %s" % (dir, e))
    return


def write_file(filename, content, mode=None, compress=None,
               create_directory=False, logger=LOGGER):
    """Atomically write content into the specified filename.

    The content is written into a temp file in the same directory as
    filename, and then swapped into place with rename.  This assumes
    that both the file and the directory can be written to by the
    broker.  The same directory was used instead of a temporary
    directory because atomic swaps are generally only available when
    the source and the target are on the same filesystem.

    If mode is set, change permissions on the file (newly created or
    pre-existing) to the new mode.  If unset and the file exists, the
    current permissions will be kept.  If unset and the file is new,
    the default is 0644.

    This method may raise OSError if any of the OS-related methods
    (creating the temp file, writing to it, correcting permissions,
    swapping into place) fail.  The method will attempt to remove
    the temp file if it had been created.

    If the compress keyword is passed, the content is compressed in
    memory before writing.  The only compression currently supported
    is gzip.

    """
    if compress == 'gzip':
        config = Config()
        buffer = StringIO()
        compress = config.getint('broker', 'gzip_level')
        zipper = gzip.GzipFile(filename, 'wb', compress, buffer)
        zipper.write(content)
        zipper.close()
        content = buffer.getvalue()
    if mode is None:
        try:
            old_mode = os.stat(filename).st_mode
        except OSError, e:
            old_mode = 0644
    dirname, basename = os.path.split(filename)

    if not os.path.exists(dirname) and create_directory:
        os.makedirs(dirname)

    fd, fpath = mkstemp(prefix=basename, dir=dirname)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        if mode is None:
            os.chmod(fpath, old_mode)
        else:
            os.chmod(fpath, mode)
        os.rename(fpath, filename)
    finally:
        if os.path.exists(fpath):
            os.remove(fpath)


def read_file(path, filename, logger=LOGGER):
    fullfile = os.path.join(path, filename)
    try:
        return open(fullfile).read()
    except OSError, e:
        raise AquilonError("Could not read contents of %s: %s" % (fullfile, e))


def remove_file(filename, cleanup_directory=False, logger=LOGGER):
    try:
        os.remove(filename)
    except OSError, e:
        if e.errno != errno.ENOENT:
            logger.info("Could not remove file '%s': %s" % (filename, e))
    if cleanup_directory:
        try:
            os.removedirs(os.path.dirname(filename))
        except OSError:
            pass
