# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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
""" Helper functions for personality """


from aquilon.exceptions_ import AuthorizationException
from aquilon.aqdb.model import Personality, Host, HostEnvironment
from aquilon.worker.commands.deploy import validate_justification
from sqlalchemy.orm.session import object_session


def is_prod_personality_used(dbpersona):

     session = object_session(dbpersona)
     q = session.query(Host.hardware_entity_id).filter_by(personality=dbpersona)

     if dbpersona.host_environment.name == 'prod' and q.count() > 0:
        return True

     return False

def validate_personality_justification(dbpersona, user, justification, reason):
     if is_prod_personality_used(dbpersona):
         if not justification:
             raise AuthorizationException(
                   "{0} is marked production and is under "
                   "change management control. Please specify "
                   "--justification or --justification='emergency' and reason.".format(dbpersona))

         validate_justification(user, justification, reason)
