# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016  Contributor
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

from aquilon.exceptions_ import ArgumentError, NotFoundException, AquilonError
from aquilon.aqdb.model import SingleInstanceMixin


class LifecycleEngine(SingleInstanceMixin):
    transitions = {}  # Override in derived class!

    def transition(self, obj, target_stage):
        '''Transition to another lifecycle stage.

        obj -- the object which wants to change stage
        target_stage -- a db object referring to the desired stage

        returns a list of objects that have changed stage.
        throws an ArgumentError exception if the stage cannot
        be reached. This method may be subclassed by stage
        if there is special logic regarding the transition.
        If the current stage has an onLeave method, then the
        method will be called with the object as an argument.
        If the target stage has an onEnter method, then the
        method will be called with the object as an argument.

        '''

        if target_stage.name == self.name:
            return False

        if target_stage.name not in self.__class__.transitions:
            raise AquilonError("stage of %s is invalid" % target_stage.name)

        targets = sorted(self.__class__.transitions[self.name])
        if target_stage.name not in targets:
            raise ArgumentError("Cannot change lifecycle stage to %s from %s. "
                                "Legal states are: %s" %
                                ( target_stage.name, self.name,
                                 ", ".join(targets)))

        obj.lifecycle = target_stage
        object_session(obj).add(obj)
        return True
