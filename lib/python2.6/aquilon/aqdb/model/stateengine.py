# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011  Contributor
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
from sqlalchemy.orm.session import Session, object_session
from aquilon.exceptions_ import ArgumentError, NotFoundException


class StateEngine:
    transitions = {}  # Override in derived class!

    def transition(self, obj, target_state):
        '''Transition to another state.

        obj -- the object which wants to change state
        target_state -- a db object referring to the desired state

        returns a list of objects that have changed state.
        throws an ArgumentError exception if the state cannot
        be reached. This method may be subclassed by states
        if there is special logic regarding the transition.
        If the current state has an onLeave method, then the
        method will be called with the object as an argument.
        If the target state has an onEnter method, then the
        method will be called with the object as an argument.

        '''

        if target_state.name == self.name:
            return False

        if target_state.name not in self.__class__.transitions:
            raise ArgumentError("status of %s is invalid" % target_state.name)

        targets = self.__class__.transitions[self.name]
        if target_state.name not in targets:
            raise ArgumentError(("cannot change state to %s from %s. " +
                   "Legal states are: %s") % (target_state.name, self.name,
                   ", ".join(targets)))

        if hasattr(self, 'onLeave'):
            self.onLeave(obj)
        obj.status = target_state
        object_session(obj).add(obj)
        if hasattr(target_state, 'onEnter'):
            target_state.onEnter(obj)
        return True

    @classmethod
    def get_unique(cls, session, name, **kwargs):
        '''override the Base get_unique to deal with simple polymorphic table

        The API is simpler: only a single positional argument is supported.
        '''

        if not isinstance(session, Session):  # pragma: no cover
            raise TypeError("The first argument of get_unique() must be an "
                            "SQLAlchemy session.")

        compel = kwargs.get('compel', False)
        preclude = kwargs.pop('preclude', False)
        clslabel = "state"

        if name not in cls.transitions:
            if not compel:
                return None
            msg = "%s %s not found." % (clslabel, name)
            raise NotFoundException(msg)

        query = session.query(cls).filter(getattr(cls, "name") == name)
        # We can't get NoResultFound since we've already checked the transition
        # table, and we can't get MultipleResultsFound since name is unique.
        obj = query.one()
        if preclude:
            msg = "%s %s already exists." % (clslabel, name)
            raise ArgumentError(msg)
        return obj
