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

from sqlalchemy import Integer, Column, ForeignKey

from aquilon.aqdb.model import Resource

_TN = 'application'


class Application(Resource):
    """ Application resources """
    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': _TN}

    id = Column(Integer, ForeignKey('resource.id',
                                    name='app_resource_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

    eonid = Column(Integer, nullable=False)

application = Application.__table__
application.info['unique_fields'] = ['name', 'holder']
