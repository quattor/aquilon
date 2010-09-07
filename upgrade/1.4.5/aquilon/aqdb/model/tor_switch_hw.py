# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
""" Top of Rack Swtiches """
from datetime import datetime

from sqlalchemy      import Table, Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm  import relation, deferred, backref

from aquilon.aqdb.model import HardwareEntity

#TODO: use selection of the tor_switch_hw specs to dynamically populate
#      default values for all of the attrs where its possible

class TorSwitchHw(HardwareEntity):
    __tablename__ = 'tor_switch_hw'
    __mapper_args__ = {'polymorphic_identity': 'tor_switch'}

    #TODO: rename to id?
    hardware_entity_id = Column(Integer,
                                ForeignKey('hardware_entity.id',
                                           name='tor_switch_hw_ent_fk',
                                           ondelete='CASCADE'),
                                           primary_key=True)

    last_poll = Column(DateTime, nullable=False, default=datetime.now)

    @property
    def hardware_name(self):
        if self.tor_switch:
            return ",".join(tor_switch.fqdn for tor_switch in self.tor_switch)
        return self._hardware_name

tor_switch_hw = TorSwitchHw.__table__
tor_switch_hw.primary_key.name='tor_switch_hw_pk'

table = tor_switch_hw

#TODO: make tor_switch_hw --like [other tor_switch_hw] + overrides


