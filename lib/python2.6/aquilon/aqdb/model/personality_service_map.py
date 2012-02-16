# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011  Contributor
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
""" Maps service instances to locations. See class.__doc__ """

from datetime import datetime

from sqlalchemy import (Column, Integer, Sequence, String, DateTime, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.model import Base, Location, Personality, ServiceInstance

_TN = 'personality_service_map'
_ABV = 'prsnlty_svc_map'


class PersonalityServiceMap(Base):
    """ Personality Service Map: mapping a service_instance to a location,
        qualified by a personality.The rows in this table assert that an
        instance is a valid useable default that clients of the given
        personality can choose as their provider during service
        autoconfiguration. """

    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_seq' % _ABV), primary_key=True)

    service_instance_id = Column(Integer, ForeignKey('service_instance.id',
                                                     name='%s_svc_inst_fk' % _ABV,
                                                     ondelete='CASCADE'),
                                 nullable=False)

    location_id = Column(Integer, ForeignKey('location.id', ondelete='CASCADE',
                                             name='%s_loc_fk' % _ABV),
                         nullable=False)

    personality_id = Column(Integer, ForeignKey('personality.id',
                                                name='personality',
                                                ondelete='CASCADE'),
                            nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now, nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    location = relation(Location, innerjoin=True,
                        backref=backref('personality_service_maps', lazy=True,
                                        cascade="all, delete-orphan"))
    service_instance = relation(ServiceInstance, innerjoin=True,
                                backref=backref('personality_service_map',
                                                lazy=True,
                                                cascade="all, delete-orphan"))
    personality = relation(Personality, uselist=False, innerjoin=True,
                           backref=backref('maps', lazy=True,
                                           cascade="all, delete-orphan"))

    #Archetype probably shouldn't be exposed at this table/object: This isn't
    #intended for use with Archetype, but I'm not 100% sure yet
    #def _archetype(self):
    #    return self.personality.archetype
    #archetype = property(_archetype)

    @property
    def service(self):
        return self.service_instance.service


psm = PersonalityServiceMap.__table__  # pylint: disable=C0103, E1101
psm.primary_key.name = 'prsnlty_svc_map_pk'

#TODO: reconsider the surrogate primary key?
psm.append_constraint(
    UniqueConstraint('personality_id', 'service_instance_id', 'location_id',
                     name='%s_loc_inst_uk' % _ABV))
