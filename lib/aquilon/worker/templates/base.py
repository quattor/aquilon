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
"""Any work by the broker to write out (or read in?) templates lives here."""


import os
import logging

from mako.lookup import TemplateLookup

from sqlalchemy.inspection import inspect

from aquilon.exceptions_ import InternalError, IncompleteError
from aquilon.config import Config
from aquilon.aqdb.model import Base
from aquilon.worker.locks import lock_queue, CompileKey
from aquilon.worker.templates.panutils import pan_assign, pan_variable
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.utils import write_file, read_file, remove_file

LOGGER = logging.getLogger(__name__)

_config = Config()
TEMPLATE_EXTENSION = _config.get("panc", "template_extension")


class Plenary(object):

    template_type = ""
    """ Specifies the PAN template type to generate """

    handlers = {}
    """ The handlers dictionary should have an entry for every subclass.
        Typically this will be defined immediately after defining the
        subclass.

    """
    def __init__(self, dbobj, logger=LOGGER):
        super(Plenary, self).__init__()

        if not dbobj:
            raise ValueError("A plenary instance must be bound to a DB object.")

        self.config = Config()
        self.dbobj = dbobj
        self.logger = logger

        self.new_content = None

        # The following attributes are for stash/restore_stash
        self.old_path = self.full_path(dbobj)
        self.old_content = None
        self.old_mtime = None
        self.stashed = False
        self.removed = False
        self.changed = False

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
        return "%s(%s)" % (self.__class__.__name__, self.dbobj)

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
        return _config.get("broker", "plenarydir")

    @classmethod
    def full_path(cls, dbobj):
        """ Full absolute path name of the plenary template """
        loadpath = cls.loadpath(dbobj)
        if loadpath:
            return "%s/%s/%s%s" % (cls.base_dir(dbobj), loadpath,
                                   cls.template_name(dbobj), TEMPLATE_EXTENSION)
        else:
            return "%s/%s%s" % (cls.base_dir(dbobj), cls.template_name(dbobj),
                                TEMPLATE_EXTENSION)

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

    def will_change(self):
        self.stash()
        if not self.new_content:
            self.new_content = self._generate_content()
        return self.old_content != self.new_content

    def get_write_key(self):
        # This is a hack to handle the case when the DB object has been deleted,
        # but a plenary instance still references it (probably buried inside a
        # PlenaryCollection). Calling self.will_change() on such a plenary would
        # fail, because the primary key is None, which is otherwise impossible.
        if isinstance(self.dbobj, Base):
            state = inspect(self.dbobj)
            if state.deleted:
                return None

        if self.will_change():
            return self.get_key()
        return None

    def get_remove_key(self):
        """Return the relevant key.

        In many cases it will be more efficient just to create a full
        compile lock and bypass this method.

        """
        return self.get_key()

    def get_key(self):
        """Base implementation assumes a full compile lock."""
        return CompileKey(logger=self.logger)

    def _generate_content(self):
        lines = []
        type = self.template_type
        if type:
            type = type + " "

        lines.append("%stemplate %s;" % (type, self.template_name(self.dbobj)))
        lines.append("")

        self.body(lines)

        return "\n".join(lines) + "\n"

    def write(self, locked=False):
        """Write out the template.

        If the content is unchanged, then the file will not be modified
        (preserving the mtime).

        Returns the number of files that were written.

        If locked is True then it is assumed that error handling happens
        higher in the call stack.

        """

        if self.template_type == "object" and \
           hasattr(self.dbobj, "personality") and \
           self.dbobj.personality and \
           not self.dbobj.personality.archetype.is_compileable:
            return 0

        # This is a hack to handle the case when the DB object has been deleted,
        # but a plenary instance still references it (probably buried inside a
        # PlenaryCollection). Calling self.will_change() on such a plenary would
        # fail, because the primary key is None, which is otherwise impossible.
        if isinstance(self.dbobj, Base):
            state = inspect(self.dbobj)
            if state.deleted:
                return 0

        if not self.new_content:
            self.new_content = self._generate_content()
        content = self.new_content

        key = None
        try:
            if not locked:
                key = self.get_write_key()
                lock_queue.acquire(key)

            self.stash()

            if self.old_content == content and \
               not self.removed and not self.changed:
                # optimise out the write (leaving the mtime good for ant)
                # if nothing is actually changed
                return 0

            path = self.full_path(self.dbobj)
            dirname = os.path.dirname(path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            write_file(path, content, logger=self.logger)
            self.removed = False
            if self.old_content != content:
                self.changed = True
        except Exception, e:
            if not locked:
                self.restore_stash()
            raise e
        finally:
            if not locked:
                lock_queue.release(key)

        return 1

    def read(self):
        return read_file("", self.old_path, logger=self.logger)

    def remove(self, locked=False, remove_profile=False):
        """
        remove this plenary template
        """

        key = None
        try:
            if not locked:
                key = self.get_remove_key()
                lock_queue.acquire(key)
            self.stash()

            remove_file(self.old_path, logger=self.logger)
            try:
                os.removedirs(os.path.dirname(self.old_path))
            except OSError:
                pass
            self.removed = True
        # Most of the error handling routines would restore_stash...
        # but there's no need here if the remove failed. :)
        finally:
            if not locked:
                lock_queue.release(key)
        return

    def stash(self):
        """Record the state of the plenary to make restoration possible.

        This should only be called while holding an appropriate lock.

        """
        if self.stashed:
            return
        try:
            self.old_content = self.read()
            self.old_mtime = os.stat(self.old_path).st_atime
        except IOError:
            self.old_content = None
        self.stashed = True

    def restore_stash(self):
        """Restore previous state of plenary.

        This should only be called while holding an appropriate lock.

        """
        if not self.stashed:
            self.logger.info("Attempt to restore plenary '%s' "
                             "without having saved state." % self.old_path)
            return
        # Should this optimization be in use?
        # if not self.changed and not self.removed:
        #    return
        dirname = os.path.dirname(self.old_path)
        if self.old_content is None:
            remove_file(self.old_path, logger=self.logger)
            try:
                os.removedirs(dirname)
            except OSError:
                pass
        else:
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            write_file(self.old_path, self.old_content, logger=self.logger)
            atime = os.stat(self.old_path).st_atime
            os.utime(self.old_path, (atime, self.old_mtime))

    @staticmethod
    def get_plenary(dbobj, logger=LOGGER):
        if dbobj.__class__ not in Plenary.handlers:
            raise InternalError("Class %s does not have a plenary handler" %
                                dbobj.__class__.__name__)
        return Plenary.handlers[dbobj.__class__](dbobj, logger=logger)

    def set_logger(self, logger):
        self.logger = logger


class StructurePlenary(Plenary):

    template_type = "structure"


class ObjectPlenary(Plenary):

    template_type = "object"

    def __init__(self, dbobj=None, logger=LOGGER):
        if not dbobj or not hasattr(dbobj, "branch"):
            raise InternalError("Plenaries meant to be compiled need a DB "
                                "object that has a branch; got: %r" % dbobj)

        super(ObjectPlenary, self).__init__(dbobj, logger)

        self.old_name = self.template_name(dbobj)
        self.old_branch = dbobj.branch.name

    @classmethod
    def loadpath(cls, dbobj):
        """ Return the default LOADPATH for this object profile """
        return dbobj.personality.archetype.name

    @classmethod
    def base_dir(cls, dbobj):
        return os.path.join(_config.get("broker", "builddir"),
                            "domains", dbobj.branch.name, "profiles")

    @classmethod
    def full_path(cls, dbobj):
        # loadpath is interpreted differently for object templates, it's not
        # parth of the full path
        return "%s/%s%s" % (cls.base_dir(dbobj), cls.template_name(dbobj),
                            TEMPLATE_EXTENSION)

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
        if self.dbobj.branch.branch_type == 'sandbox':
            pan_assign(lines, "/metadata/template/branch/author",
                       self.dbobj.sandbox_author.name)
        lines.append("")

        self.body(lines)

        return "\n".join(lines) + "\n"

    def remove(self, locked=False, remove_profile=False):
        """
        remove all files related to an object template including
        any intermediate build files
        """
        key = None
        try:
            if not locked:
                key = self.get_remove_key()
                lock_queue.acquire(key)
            self.stash()

            # Only one or the other of .xml/.xml.gz should be there...
            # it doesn't hurt to clean up both.
            # .xml.dep is used up to and including panc 9.2
            # .dep is used by panc 9.4 and higher
            basename = os.path.join(self.config.get("broker", "quattordir"),
                                    "build", self.old_branch, self.old_name)
            for ext in (".xml", ".xml.gz", ".xml.dep", ".dep"):
                remove_file(basename + ext, logger=self.logger)
            try:
                os.removedirs(os.path.dirname(basename))
            except OSError:
                pass

            super(ObjectPlenary, self).remove(locked=True)

            if remove_profile:
                basename = os.path.join(self.config.get("broker",
                                                        "profilesdir"),
                                        self.old_name)
                # Only one of these should exist, but it doesn't hurt
                # to try to clean up both.
                for ext in (".xml", ".xml.gz"):
                    remove_file(basename + ext, logger=self.logger)

                # Remove the cached template created by ant
                remove_file(os.path.join(self.config.get("broker",
                                                         "quattordir"),
                                         "objects",
                                         self.old_name + TEMPLATE_EXTENSION),
                            logger=self.logger)
        except:
            if not locked:
                self.restore_stash()
            raise
        finally:
            if not locked:
                lock_queue.release(key)


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
    def __init__(self, logger=LOGGER):
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
        return "PlenaryCollection(%s)" % ", ".join([str(plenary) for plenary
                                                    in self.plenaries])

    def __iter__(self):
        for plen in self.plenaries:
            yield plen

    def get_write_key(self):
        keylist = []
        for plen in self.plenaries:
            keylist.append(plen.get_write_key())
        return CompileKey.merge(keylist)

    def get_remove_key(self):
        keylist = []
        for plen in self.plenaries:
            keylist.append(plen.get_remove_key())
        return CompileKey.merge(keylist)

    def get_key(self):
        # get_key doesn't make any sense for a plenary collection...
        raise InternalError("get_key called on PlenaryCollection")

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
            elif plen.template_type == 'object':
                yield plen.template_name(plen.dbobj)

    def write(self, locked=False):
        # If locked is True, assume error handling happens higher
        # in the stack.
        total = 0
        # Pre-stash all plenaries before attempting to write any
        # of them.  This way if an error occurs all can go through
        # the same restore logic.
        self.stash()
        key = None
        try:
            if not locked:
                key = self.get_write_key()
                lock_queue.acquire(key)
            for plen in self.plenaries:
                # IncompleteError is almost pointless in this context, but
                # it has the nice side effect of not updating the total.
                try:
                    total += plen.write(locked=True)
                except IncompleteError, err:
                    self.logger.client_info("Warning: %s" % err)
        except:
            if not locked:
                self.restore_stash()
            raise
        finally:
            if not locked:
                lock_queue.release(key)
        return total

    def remove(self, locked=False, remove_profile=False):
        self.stash()
        key = None
        try:
            if not locked:
                key = self.get_remove_key()
                lock_queue.acquire(key)
            for plen in self.plenaries:
                plen.remove(locked=True, remove_profile=remove_profile)
        except:
            if not locked:
                self.restore_stash()
            raise
        finally:
            if not locked:
                lock_queue.release(key)

    def read(self):
        # This should never be called, but we put it here
        # just in-case, since the Plenary method is inappropriate.
        raise InternalError("read called on PlenaryCollection")

    def set_logger(self, logger):
        for plen in self.plenaries:
            plen.set_logger(logger)

    def append(self, plenary):
        plenary.set_logger(self.logger)
        self.plenaries.append(plenary)

    def extend(self, iterable):
        for plenary in iterable:
            plenary.set_logger(self.logger)
            self.plenaries.append(plenary)


class TemplateFormatter(ObjectFormatter):

    def __init__(self):
        super(TemplateFormatter, self).__init__()
        self.mako_dir = os.path.join(self.config.get("broker", "srcdir"), "lib",
                                     "aquilon", "worker", "templates", "mako")
        self.lookup_raw = TemplateLookup(directories=[os.path.join(self.mako_dir, "raw")],
                                         imports=['from string import rstrip',
                                                  'from '
                                                  'aquilon.worker.formats.formatters '
                                                  'import shift'],
                                         default_filters=['unicode', 'rstrip'])
