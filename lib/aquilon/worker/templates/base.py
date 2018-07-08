# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
"""Any work by the broker to write out (or read in?) templates lives here."""

import os
import errno
import logging
import threading
import weakref
from contextlib import contextmanager

from sqlalchemy.inspection import inspect
from sqlalchemy.orm import object_session

from aquilon.exceptions_ import (InternalError, IncompleteError,
                                 NotFoundException, ArgumentError)
from aquilon.config import Config
from aquilon.aqdb.model import Base, Sandbox, CompileableMixin
from aquilon.worker.locks import lock_queue, CompileKey, NoLockKey
from aquilon.worker.templates.panutils import pan_assign, pan_variable
from aquilon.utils import write_file, remove_file

LOGGER = logging.getLogger(__name__)

# Maintain a cache of plenaries, to avoid creating multiple plenary objects
# referencing the same file. The cache is per-thread, to avoid mixing objects
# from different sessions.
_mylocal = threading.local()


class Plenary(object):
    template_type = "unique"
    """ Specifies the PAN template type to generate """

    handlers = {}
    """ The handlers dictionary should have an entry for every subclass.
        Typically this will be defined immediately after defining the
        subclass.

    """

    prefix = None
    """ Path prefix used to check conflicts with e.g. archetype names """

    config = Config()
    TEMPLATE_EXTENSION = config.get("panc", "template_extension")

    ignore_compileable = False
    """ Force generating the plenary even if it belongs to a non-compileable
        object
    """

    def __init__(self, dbobj, logger=LOGGER, allow_incomplete=True):
        super(Plenary, self).__init__()

        if not dbobj:
            raise ValueError("A plenary instance must be bound to a DB object.")

        self.dbobj = dbobj
        self.logger = logger

        # We may no longer be able to calculate this during remove()
        try:
            self.debug_name = str(dbobj.qualified_name)
        except AttributeError:
            self.debug_name = str(dbobj)

        # The following attributes are for stash/restore_stash
        self.old_path = self.full_path(dbobj)
        self.new_path = None
        self.old_content = None
        self.stashed = False
        self.removed = False
        self.changed = False
        self.allow_incomplete = allow_incomplete

    def __hash__(self):
        """Since equality is based on dbobj, just hash on it."""
        return hash(self.dbobj)

    def __eq__(self, other):
        """Plenary objects are equal if they describe the same object.

        Technically this should probably also check that the class
        matches.  There are some odd cases when the plenary stores
        extra information, currently ignored.

        """
        if self.dbobj is None or other.dbobj is None:
            return False
        return self.dbobj == other.dbobj

    def __repr__(self):
        """For debug output."""
        return "%s(%s)" % (self.__class__.__name__, self.debug_name)

    @classmethod
    def template_name(cls, dbobj):  # pylint: disable=W0613
        """ Name of the template as used by PAN, relative to the load path """
        raise InternalError("%s must override the template_name() method." %
                            cls.__name__)

    @classmethod
    def loadpath(cls, dbobj):  # pylint: disable=W0613
        """ Return the LOADPATH the template is relative to """
        return ""

    @classmethod
    def base_dir(cls, dbobj):  # pylint: disable=W0613
        """ Base directory of the plenary template """
        return cls.config.get("broker", "plenarydir")

    @classmethod
    def full_path(cls, dbobj):
        """ Full absolute path name of the plenary template """
        loadpath = cls.loadpath(dbobj)
        if loadpath:
            return "%s/%s/%s%s" % (cls.base_dir(dbobj), loadpath,
                                   cls.template_name(dbobj), cls.TEMPLATE_EXTENSION)
        else:
            return "%s/%s%s" % (cls.base_dir(dbobj), cls.template_name(dbobj),
                                cls.TEMPLATE_EXTENSION)

    def body(self, lines):
        """
        The text of the template. By default, do nothing. A derived class can
        override this to describe their own content.
        They should do this by appending strings (each string
        referring to a separate line of text in the template) into the
        array. The array will already contain the appropriate header line for the
        template.
        """
        pass

    def get_key(self, exclusive=True):  # pylint: disable=W0613
        return NoLockKey(logger=self.logger)

    def _generate_content(self):
        lines = []
        type = self.template_type
        if type:
            type = type + " "

        lines.append("%stemplate %s;" % (type, self.template_name(self.dbobj)))
        lines.append("")

        self.body(lines)

        return "\n".join(lines) + "\n"

    def is_deleted(self):
        session = object_session(self.dbobj)
        return self.dbobj in session.deleted or inspect(self.dbobj).deleted

    def is_dirty(self):
        session = object_session(self.dbobj)
        return self.dbobj in session.dirty

    def _write(self, remove_profile=False):
        """Write out the template.

        If the content is unchanged, then the file will not be modified
        (preserving the mtime).

        Returns the number of files that were written.
        """

        if isinstance(self.dbobj, CompileableMixin) and \
           not self.ignore_compileable and \
           not self.dbobj.archetype.is_compileable:
            return self._remove(remove_profile=True)

        self.stash()

        if self.is_deleted():
            return self._remove(remove_profile=remove_profile)
        elif not self.new_path:
            raise InternalError("{0!r}: object is not deleted, but "
                                "new_path is not set.".format(self))

        try:
            content = self._generate_content()
        except IncompleteError as err:
            self._remove()
            if self.allow_incomplete:
                self.logger.client_info("Warning: %s", err)
                return 0
            else:
                raise

        if self.old_content == content and not self.removed:
            # optimise out the write (leaving the mtime good for ant)
            # if nothing is actually changed
            return 0

        # If the plenary has moved, then clean up any potential leftover
        # files from the old location
        if self.new_path != self.old_path:
            self._remove()

        self.logger.debug("Writing %r [%s]", self, self.new_path)

        write_file(self.new_path, content, create_directory=True,
                   logger=self.logger)
        self.changed = True
        if self.new_path == self.old_path:
            self.removed = False

        return 1

    def read(self):
        int_error = lambda e: \
            InternalError("Error reading plenary file %s: %s" %
                          (self.old_path, e.strerror))
        try:
            return open(self.old_path).read()
        except IOError as e:
            # Unable to open the file
            if e.errno == errno.ENOENT:
                raise NotFoundException("Pleanary file %s not found" %
                                        self.old_path)
            else:
                raise int_error(e)
        except OSError as e:
            # Read has failed, which shouldn't happen unless there is a problem
            raise int_error(e)

    def _remove(self, remove_profile=False):  # pylint: disable=W0613
        """
        remove this plenary template
        """

        if os.path.exists(self.old_path):
            self.logger.debug("Removing %r [%s]", self, self.old_path)
        if remove_file(self.old_path, cleanup_directory=True,
                       logger=self.logger):
            self.removed = True
        return 1

    def stash(self):
        """Record the state of the plenary to make restoration possible.

        This should only be called while holding an appropriate lock.

        """
        if self.stashed:
            return

        if self.is_dirty():
            raise InternalError("{0!r}: stash() is called on dirty object"
                                .format(self))

        # If the object is already deleted, then it may not have enough state
        # for generating the path.
        if not self.is_deleted():
            self.new_path = self.full_path(self.dbobj)

        try:
            self.old_content = self.read()
        except NotFoundException:
            self.old_content = None
        self.stashed = True

    def restore_stash(self):
        """Restore previous state of plenary.

        This should only be called while holding an appropriate lock.

        """
        if not self.stashed:
            self.logger.info("Attempt to restore plenary '%s' "
                             "without having saved state.", self.old_path)
            return

        # If the plenary has moved, then we need to clean up the new location
        if self.new_path and self.new_path != self.old_path:
            self.logger.debug("Removing %r [%s]", self, self.new_path)
            remove_file(self.new_path, cleanup_directory=True,
                        logger=self.logger)

        self.logger.debug("Restoring %r [%s]", self, self.old_path)
        if self.old_content is None:
            remove_file(self.old_path, cleanup_directory=True,
                        logger=self.logger)
        else:
            write_file(self.old_path, self.old_content, create_directory=True,
                       logger=self.logger)
            # Do not try to restore the timestamp of the plenary. If the
            # rollback is due to just a couple of profiles failing from a large
            # batch, we want the next domain compile to recompile the hosts that
            # did not fail here. Otherwise, the domain compile would push out
            # the state that got reverted in the DB.

        self.removed = False
        self.changed = False

    @classmethod
    def get_plenary(cls, dbobj, logger=LOGGER, allow_incomplete=True):
        if cls == Plenary:
            if dbobj.__class__ not in Plenary.handlers:
                raise InternalError("Class %s does not have a plenary handler" %
                                    dbobj.__class__.__name__)
            handler = Plenary.handlers[dbobj.__class__]
        else:
            handler = cls

        if not hasattr(_mylocal, "plenaries"):
            _mylocal.plenaries = weakref.WeakValueDictionary()

        key = (handler, dbobj)
        try:
            return _mylocal.plenaries[key]
        except KeyError:
            plenary = handler(dbobj, logger=logger,
                              allow_incomplete=allow_incomplete)
            _mylocal.plenaries[key] = plenary
            return plenary

    def set_logger(self, logger):
        self.logger = logger


class StructurePlenary(Plenary):

    template_type = "structure"


class ObjectPlenary(Plenary):

    template_type = "object"

    # We want to remove all possible extensions generated by panc when a profile
    # is to be removed
    cleanup_extensions = (".dep", ".xml", ".xml.gz", ".json", ".json.gz")

    def __init__(self, dbobj=None, **kwargs):
        if not dbobj or not hasattr(dbobj, "branch"):
            raise InternalError("Plenaries meant to be compiled need a DB "
                                "object that has a branch; got: %r" % dbobj)

        super(ObjectPlenary, self).__init__(dbobj, **kwargs)

        self.old_name = self.template_name(dbobj)
        self.old_branch = dbobj.branch.name

    @classmethod
    def loadpath(cls, dbobj):
        """ Return the default LOADPATH for this object profile """
        return dbobj.archetype.name

    @classmethod
    def base_dir(cls, dbobj):
        return os.path.join(cls.config.get("broker", "cfgdir"),
                            "domains", dbobj.branch.name, "profiles")

    @classmethod
    def full_path(cls, dbobj):
        # loadpath is interpreted differently for object templates, it's not
        # parth of the full path
        return "%s/%s%s" % (cls.base_dir(dbobj), cls.template_name(dbobj),
                            cls.TEMPLATE_EXTENSION)

    def get_key(self, exclusive=True):
        if not exclusive:
            # CompileKey() does not support shared mode
            raise InternalError("Shared locks are not implemented for object "
                                "plenaries.")

        return CompileKey(domain=self.old_branch, profile=self.old_name,
                          logger=self.logger)

    def _generate_content(self):
        lines = []
        lines.append("object template %s;" % self.template_name(self.dbobj))
        lines.append("")

        loadpath = self.loadpath(self.dbobj)
        if loadpath:
            pan_variable(lines, "LOADPATH", [loadpath])
            lines.append("")
        pan_assign(lines, "/metadata/template/branch/name",
                   self.dbobj.branch.name)
        pan_assign(lines, "/metadata/template/branch/type",
                   self.dbobj.branch.branch_type)
        if isinstance(self.dbobj.branch, Sandbox):
            if not self.dbobj.sandbox_author:
                raise IncompleteError("{0} is missing sandbox author "
                                      "information.".format(self.dbobj))
            pan_assign(lines, "/metadata/template/branch/author",
                       self.dbobj.sandbox_author.name)
        lines.append("")

        self.body(lines)

        return "\n".join(lines) + "\n"

    def _remove(self, remove_profile=False):
        """
        remove all files related to an object template including
        any intermediate build files
        """
        basename = os.path.join(self.config.get("broker", "quattordir"),
                                "build", self.old_branch, self.old_name)
        for ext in self.cleanup_extensions:
            remove_file(basename + ext, logger=self.logger)
        try:
            os.removedirs(os.path.dirname(basename))
        except OSError:
            pass

        super(ObjectPlenary, self)._remove()

        if remove_profile:
            basename = os.path.join(self.config.get("broker", "profilesdir"),
                                    self.old_name)
            for ext in self.cleanup_extensions:
                remove_file(basename + ext, logger=self.logger)

            # Remove the cached template created by ant
            remove_file(os.path.join(self.config.get("broker", "quattordir"),
                                     "objects",
                                     self.old_name + self.TEMPLATE_EXTENSION),
                        logger=self.logger)
        return 1


class PlenaryCollection(object):
    """
    A collection of plenary templates, presented behind a single
    facade to make them appear as one template to the caller.

    One use is for objects that logically have multiple plenary files
    to subclass from this and append the real template objects into
    self.plenaries.

    Another is for commands to use this object directly for its
    convenience methods around writing and rolling back plenary
    templates.

    This object cannot handle cases like a plenary file that
    changes location, but it could handle storing a group of plenaries
    that need to be removed and a second collection could handle another
    group that needs to be written.

    """
    def __init__(self, logger=LOGGER, allow_incomplete=True):  # pylint: disable=W0613
        super(PlenaryCollection, self).__init__()

        self.plenaries = []
        self.logger = logger

    def __hash__(self):
        """The hash just needs to be ballpark (and not clash with __eq__)."""
        if self.plenaries:
            return hash(self.plenaries[0])
        return hash(None)

    def __eq__(self, other):
        """Two collections are equal if they have all the same members.

        This currently requires that the order by the same.  It's good
        enough for now - really we just want (for example) the
        ServiceInstance plenary collection to evaluate as equal, and
        those members will always be defined in the same order.

        """
        if len(self.plenaries) != len(other.plenaries):
            return False
        for (i, j) in zip(self.plenaries, other.plenaries):
            if i != j:
                return False
        return True

    def __str__(self):
        """For debug output."""
        return "%s(%s)" % (self.__class__.__name__,
                           ", ".join(str(plenary)
                                     for plenary in self.plenaries))

    def __iter__(self):
        for plen in self.plenaries:
            yield plen

    def get_key(self, exclusive=True):
        keylist = [NoLockKey(logger=self.logger)]
        keylist.extend(plen.get_key(exclusive=exclusive)
                       for plen in self.plenaries)
        return CompileKey.merge(keylist)

    def stash(self):
        for plen in self.plenaries:
            plen.stash()

    def restore_stash(self):
        for plen in self.plenaries:
            plen.restore_stash()

    @property
    def object_templates(self):
        for plen in self.plenaries:
            if isinstance(plen, PlenaryCollection):
                for obj in plen.object_templates:
                    yield obj
            elif plen.template_type == 'object' and plen.dbobj.archetype.is_compileable:
                yield plen.template_name(plen.dbobj)

    def _write(self, remove_profile=False):
        total = 0
        errors = []
        for plen in self.plenaries:
            try:
                total += plen._write(remove_profile=remove_profile)
            except IncompleteError as err:
                errors.append(str(err))

        if errors:
            raise ArgumentError("\n".join(errors))
        return total

    def write(self, locked=False, remove_profile=True, verbose=False):
        # If locked is True, assume error handling happens higher
        # in the stack.
        total = 0
        key = None
        try:
            if not locked:
                key = self.get_key()
                lock_queue.acquire(key)

            # Pre-stash all plenaries before attempting to write any
            # of them.  This way if an error occurs all can go through
            # the same restore logic.
            self.stash()

            total = self._write(remove_profile=remove_profile)
        except:
            if not locked:
                self.restore_stash()
            raise
        finally:
            if not locked:
                lock_queue.release(key)

        if verbose and self.plenaries:
            self.logger.client_info("Flushed %d/%d templates." %
                                    (total, len(self.plenaries)))
        return total

    def read(self):
        # This should never be called, but we put it here
        # just in-case, since the Plenary method is inappropriate.
        raise InternalError("read called on PlenaryCollection")

    def set_logger(self, logger):
        for plen in self.plenaries:
            plen.set_logger(logger)
        self.logger = logger

    def append(self, plenary):
        plenary.set_logger(self.logger)
        self.plenaries.append(plenary)

    def add(self, dbobj_or_iterable, allow_incomplete=True, cls=None):
        if not cls:
            cls = Plenary

        if isinstance(dbobj_or_iterable, Base):
            self.append(cls.get_plenary(dbobj_or_iterable,
                                        allow_incomplete=allow_incomplete))
        else:
            for dbobj in dbobj_or_iterable:
                self.append(cls.get_plenary(dbobj,
                                            allow_incomplete=allow_incomplete))

    def flatten(self):
        """
        Flatten embedded plenary collections.

        When reconfiguring multiple objects, we usually end up with a plenary
        collection that itself contains other plenary collections, and e.g. the
        plenaries of the same server may appear multiple times embedded in that
        tree. We still want to process those plenaries only once, so this
        operation allows flattening a tree of collections to a simple list.

        Note that there are other classes that inherit from PlenaryCollection -
        we don't want to flatten those, because those classes may add extra
        behavior in addition to being a container.
        """

        def walk_plenaries(collection_):
            for plen in collection_.plenaries:
                # Don't flatten subclasses
                if type(plen) == type(collection_):
                    for plen2 in walk_plenaries(plen):
                        yield plen2
                else:
                    yield plen

        self.plenaries = list(set(walk_plenaries(self)))

    @contextmanager
    def transaction(self, verbose=False):
        with self.get_key():
            self.stash()
            try:
                count = self.write(locked=True)
                yield
                # Do the logging only if the transaction succeeded
                if verbose:
                    self.logger.client_info("Flushed %d/%d templates." %
                                            (count, len(self.plenaries)))
            except:
                self.restore_stash()
                raise


def add_location_info(lines, dblocation, prefix="", use_rack_fullname=False):
    # FIXME: sort out hub/region
    for parent_type in ["continent", "country", "city", "campus", "building",
                        "bunker"]:
        dbparent = getattr(dblocation, parent_type)
        if dbparent:
            pan_assign(lines, prefix + "sysloc/" + parent_type, dbparent.name)

    if dblocation.rack:
        # If use_rack_fullname is True, use the rack_fullname instead of the generated rack name
        if use_rack_fullname:
            pan_assign(lines, prefix + "rack/name", dblocation.rack.fullname.lower())
        else:
            pan_assign(lines, prefix + "rack/name", dblocation.rack.name)
        if dblocation.rack_row:
            pan_assign(lines, prefix + "rack/row", dblocation.rack_row)
        if dblocation.rack_column:
            pan_assign(lines, prefix + "rack/column", dblocation.rack_column)
    if dblocation.room:
        pan_assign(lines, prefix + "sysloc/room", dblocation.room.name)
