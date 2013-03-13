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

from sqlalchemy import Integer, String, Column, Boolean, ForeignKey

from aquilon.aqdb.model import Resource

_TN = 'filesystem'


class Filesystem(Resource):
    """ Filesystem resources """
    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': 'filesystem'}

    id = Column(Integer, ForeignKey('resource.id',
                                    name='fs_resource_fk',
                                    ondelete='CASCADE'),
                                    primary_key=True)

    blockdev = Column(String(255), nullable=False)
    fstype = Column(String(32), nullable=False)
    mount = Column(Boolean(name="%s_mount_ck" % _TN),
                   default=False, nullable=False)
    mountpoint = Column(String(255), nullable=False)
    mountoptions = Column(String(255), nullable=True)
    dumpfreq = Column(Integer)
    passno = Column(Integer)


filesystem = Filesystem.__table__
filesystem.primary_key.name = '%s_pk' % (_TN)
filesystem.info['unique_fields'] = ['name', 'holder']
