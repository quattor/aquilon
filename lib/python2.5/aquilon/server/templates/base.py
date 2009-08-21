# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
"""Any work by the broker to write out (or read in?) templates lives here."""


import os
from threading import Lock

from twisted.python import log
from sqlalchemy.orm.session import object_session

from aquilon.exceptions_ import InternalError, IncompleteError
from aquilon.config import Config
from aquilon.server.processes import write_file, read_file, remove_file


# We have a global compile lock.
# This is used in two ways:
# 1) to serialize compiles. The panc java compiler does a pretty
#    good job of parallelizing, so we'll just slow things down
#    if we end up with multiple of these running.
# 2) to prevent changing plenary templates while a compile is
#    in progress

compile_lock = Lock()

def compileLock():
    log.msg("requesting compile lock")
    compile_lock.acquire()
    log.msg("aquired compile lock")

def compileRelease():
    log.msg("releasing compile lock")
    compile_lock.release()


class Plenary(object):
    def __init__(self, dbobj=None):
        self.config = Config()
        self.dbobj = dbobj
        self.template_type = 'structure'
        self.plenary_template = None
        self.plenary_core = None
        self.servername = self.config.get("broker", "servername")
        # The following attributes are for stash/restore_stash
        self.old_content = None
        self.old_mtime = None
        self.stashed = False
        self.removed = False
        self.changed = False

    def pathname(self):
        return os.path.join(self.dir, self.plenary_template + ".tpl")

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

    def write(self, dir=None, user=None, locked=False, content=None):
        """Write out the template.

        Note that session.flush() MUST be called before writing a
        changed sqlalchemy object or the embedded call to refresh
        will revert the object back to its old state.

        If the content is unchanged, then the file will not be modified
        (preserving the mtime).

        Returns the number of files that were written.

        If locked is True then it is assumed that error handling happens
        higher in the call stack.

        """

        if dir is not None:
            self.dir = dir
        # user is simply left for compatibility: it's no longer used

        if content is None:
            # This potentially calls refresh several times for objects that
            # have multiple plenaries, like service and cluster...
            self.refresh()

            lines = []
            type = self.template_type
            if type is not None and type is not "":
                type = type + " "
            lines.append("%stemplate %s;" % (type, self.plenary_template))
            lines.append("")
            self.body(lines)
            content = "\n".join(lines)+"\n"

        plenary_path = os.path.join(self.dir, self.plenary_core)
        plenary_file = self.pathname()

        try:
            if not locked:
                compileLock()
            self.stash()
            if self.old_content == content and \
               not self.removed and not self.changed:
                # optimise out the write (leaving the mtime good for ant)
                # if nothing is actually changed
                return 0
            if not os.path.exists(plenary_path):
                os.makedirs(plenary_path)
            write_file(plenary_file, content)
            self.removed = False
            if self.old_content != content:
                self.changed = True
        except Exception, e:
            if not locked:
                self.restore_stash()
            raise e
        finally:
            if not locked:
                compileRelease()

        return 1

    def read(self, dir=None):
        if dir is not None:
            self.dir = dir
        # FIXME: Dupes some logic from pathname()
        return read_file(self.dir, self.plenary_template + ".tpl")

    def remove(self, dir=None, locked=False):
        """
        remove this plenary template
        """

        if dir is not None:
            self.dir = dir

        try:
            if (not locked):
                compileLock()
            self.stash()
            remove_file(self.pathname())
            self.removed = True
        # Most of the error handling routines would restore_stash...
        # but there's no need here if the remove failed. :)
        finally:
            if (not locked):
                compileRelease()
        return

    def cleanup(self, domain, locked=False):
        """
        remove all files related to an object template including
        any intermediate build files
        """
        try:
            if not locked:
                compileLock()
            self.remove(locked=True)
            if self.template_type == "object" and hasattr(self, 'name'):
                qdir = self.config.get("broker", "quattordir")
                xmlfile = os.path.join(qdir, "build", "xml", domain,
                                       self.name + ".xml")
                remove_file(xmlfile)
                depfile = os.path.join(qdir, "build", "xml", domain,
                                       self.name + ".xml.dep")
                remove_file(depfile)
        except:
            if not locked:
                self.restore_stash()
            raise
        finally:
            if not locked:
                compileRelease()

    def refresh(self):
        """Refresh any stored database objects.

        Note that the session MUST be flushed before calling a refresh
        if the object's state has changed or it will be reverted.

        """
        # This could be enhanced to deal with dbobj being a list...
        if hasattr(self, 'dbobj') and self.dbobj:
            session = object_session(self.dbobj)
            session.refresh(self.dbobj)

    def stash(self):
        """Record the state of the plenary to make restoration possible.

        This should only be called while holding a compileLock.

        """
        if self.stashed:
            return
        try:
            self.old_content = self.read()
            self.old_mtime = os.stat(self.pathname()).st_atime
        except IOError, e:
            self.old_content = None
        self.stashed = True

    def restore_stash(self):
        """Restore previous state of plenary.

        This should only be called while holding a compileLock.

        """
        if not self.stashed:
            log.msg("Attempt to restore plenary '%s' "
                    "without having saved state." % self.pathname())
            return
        # Should this optimization be in use?
        # if not self.changed and not self.removed:
        #    return
        if (self.old_content is None):
            self.remove(locked=True)
        else:
            self.write(locked=True, content=self.old_content)
            atime = os.stat(self.pathname()).st_atime
            os.utime(self.pathname(), (atime, self.old_mtime))


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
    def __init__(self):
        self.plenaries = []

    def stash(self):
        for plen in self.plenaries:
            plen.stash()

    def restore_stash(self):
        for plen in self.plenaries:
            plen.restore_stash()

    def write(self, dir=None, user=None, locked=False, content=None):
        # If locked is True, assume error handling happens higher
        # in the stack.
        total = 0
        try:
            if not locked:
                compileLock()
            # Pre-stash all plenaries before attempting to write any
            # of them.  This way if an error occurs all can go through
            # the same restore logic.
            self.stash()
            for plen in self.plenaries:
                # IncompleteError is almost pointless in this context, but
                # it has the nice side effect of not updating the total.
                try:
                    total += plen.write(dir=dir, user=user, locked=True,
                                        content=content)
                except IncompleteError, e:
                    pass
        except:
            if not locked:
                self.restore_stash()
            raise
        finally:
            if not locked:
                compileRelease()
        return total

    def remove(self, dir=None, locked=False):
        try:
            if not locked:
                compileLock()
            self.stash()
            for plen in self.plenaries:
                plen.remove(dir, locked=True)
        except:
            if not locked:
                self.restore_stash()
            raise
        finally:
            if not locked:
                compileRelease()

    def cleanup(self, domain, locked=False):
        try:
            if not locked:
                compileLock()
            self.stash()
            for plen in self.plenaries:
                plen.cleanup(domain, locked=True)
        except:
            if not locked:
                self.restore_stash()
            raise
        finally:
            if not locked:
                compileRelease()

    def read(self):
        # This should never be called, but we put it here
        # just in-case, since the base-class method is inappropriate.
        raise InternalError

    def append(self, plenary):
        self.plenaries.append(plenary)

    def refresh(self):
        for plen in self.plenaries:
            plen.refresh()
