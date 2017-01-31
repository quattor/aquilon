# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014,2016  Contributor
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

from sqlalchemy.orm.session import object_session

from aquilon.exceptions_ import ArgumentError, AquilonError
from aquilon.aqdb.model import SingleInstanceMixin


class StateEngine(SingleInstanceMixin):
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
            raise AquilonError("status of %s is invalid" % target_state.name)

        targets = sorted(self.__class__.transitions[self.name])
        if target_state.name not in targets:
            raise ArgumentError("Cannot change state to %s from %s. "
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
