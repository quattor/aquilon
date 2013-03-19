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
""" Rack is a subclass of Location """

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import validates

from aquilon.aqdb.column_types import AqStr
from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Location


class Rack(Location):
    """ Rack is a subtype of location """
    __tablename__ = 'rack'
    __mapper_args__ = {'polymorphic_identity': 'rack'}

    id = Column(Integer, ForeignKey('location.id', name='rack_loc_fk',
                                    ondelete='CASCADE'), primary_key=True)

    rack_row = Column(AqStr(4), nullable=True)
    rack_column = Column(AqStr(4), nullable=True)

    @validates('rack_row', 'rack_column')
    def check_rack_coordinates(self, key, value):
        """ validates the row and column arguments """
        value = str(value).strip()
        if not value.isalnum():
            msg = "the value '%s' for %s must be alphanumeric" % (
                value, key)
            raise ArgumentError(msg)
        else:
            return value

rack = Rack.__table__  # pylint: disable=C0103

rack.primary_key.name = 'rack_pk'
rack.info['unique_fields'] = ['name']
