# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
from sqlalchemy.orm import reconstructor, validates

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Resource
from aquilon.aqdb.data_sync.storage import StormapParser

_TN = 'share'


class Share(Resource):
    """ Share resources """
    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': 'share'}

    id = Column(Integer, ForeignKey('resource.id',
                                    name='%s_resource_fk' % (_TN),
                                    ondelete='CASCADE'),
                primary_key=True)

    # threshold for Storage I/O Control throttle in millisecs.
    latency_threshold = Column(Integer)

    @validates('latency_threshold')
    def validate_latency_threshold(self, key, value):
        if value:
            value = int(value)
            if value != 0 and value < 20:
                raise ArgumentError("The value of %s must be either zero, or at least 20." % key)
        return value

    def __init__(self, *args, **kwargs):
        super(Share, self).__init__(*args, **kwargs)
        self._init_cache()

    @reconstructor
    def _init_cache(self):
        self._share_info = None

    @property
    def mount(self):
        if not self._share_info:
            parser = StormapParser()
            self._share_info = parser.lookup(self.name)
        return self._share_info.mount

    @property
    def server(self):
        if not self._share_info:
            parser = StormapParser()
            self._share_info = parser.lookup(self.name)
        return self._share_info.server

    def populate_share_info(self, parser):
        self._share_info = parser.lookup(self.name)


share = Share.__table__
share.info['unique_fields'] = ['name', 'holder']
