# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2013  Contributor
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
            raise ArgumentError("cannot change state to %s from %s. "
                                "Legal states are: %s" %
                                (target_state.name, self.name,
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
