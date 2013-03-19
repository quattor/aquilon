# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

    eon_id = Column(Integer, primary_key=True)

    # GRNs are case sensitive, so no AqStr here
    # TODO: is there a limit on the length of GRNs? 132 is the longest currently
    grn = Column(String(255), nullable=False)

    # If False, then assigning new objects to this GRN should fail, but old
    # objects may still point to it
    disabled = Column(Boolean(name="%s_disabled_ck" % _TN), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))


grn = Grn.__table__  # pylint: disable=C0103

grn.primary_key.name = '%s_pk' % _TN
grn.append_constraint(
    UniqueConstraint('grn', name='%s_grn_uk' % _TN))
grn.info['unique_fields'] = ['grn']
grn.info['extra_search_fields'] = ['eon_id']
