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
""" Class for mapping GRNs to EON IDs """

from datetime import datetime

from sqlalchemy import (Column, Integer, String, Boolean, UniqueConstraint,
                        DateTime)
from sqlalchemy.orm import deferred

from aquilon.aqdb.model import Base

_TN = 'grn'


class Grn(Base):
    """ Map GRNs to EON IDs """
    __tablename__ = _TN
    _instance_label = 'grn'
    _class_label = 'GRN'

    eon_id = Column(Integer, primary_key=True, autoincrement=False)

    # GRNs are case sensitive, so no AqStr here
    # TODO: is there a limit on the length of GRNs? 132 is the longest currently
    grn = Column(String(255), nullable=False)

    # If False, then assigning new objects to this GRN should fail, but old
    # objects may still point to it
    disabled = Column(Boolean(name="%s_disabled_ck" % _TN), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    __table_args__ = (UniqueConstraint(grn, name='%s_grn_uk' % _TN),)

grn = Grn.__table__  # pylint: disable=C0103
grn.info['unique_fields'] = ['grn']
grn.info['extra_search_fields'] = ['eon_id']
