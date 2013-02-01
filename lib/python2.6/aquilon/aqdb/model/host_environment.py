# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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

from datetime import datetime

from sqlalchemy.orm import deferred
from sqlalchemy import (Column, Integer, DateTime, Sequence, String,
                        UniqueConstraint)

from aquilon.aqdb.model import Base
from aquilon.exceptions_ import ArgumentError

_TN = 'host_environment'


class HostEnvironment(Base):
    """ Describes the state a host is within the provisioning lifecycle """

    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    name = Column(String(16), nullable=False)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    __mapper_args__ = {'polymorphic_on': name}

    def __repr__(self):
        return str(self.name)

    @classmethod
    def validate_name(cls, env):
        """ Utility function for command parameter parsing """
        if env in cls.__mapper__.polymorphic_map:
            return
        valid_name = ", ".join(sorted(cls.__mapper__.polymorphic_map.keys()))
        raise ArgumentError("Unknown environment value '%s'. The valid values are: "
                            "%s." % (env, valid_name))

host_env = HostEnvironment.__table__  # pylint: disable=C0103
host_env.primary_key.name = '%s_pk' % _TN
host_env.append_constraint(UniqueConstraint('name', name='%s_uk' % _TN))
host_env.info['unique_fields'] = ['name']


class Development(HostEnvironment):
    __mapper_args__ = {'polymorphic_identity': 'dev'}


class UAT(HostEnvironment):
    __mapper_args__ = {'polymorphic_identity': 'uat'}


class QA(HostEnvironment):
    __mapper_args__ = {'polymorphic_identity': 'qa'}


class Legacy(HostEnvironment):
    __mapper_args__ = {'polymorphic_identity': 'legacy'}


class Production(HostEnvironment):
    __mapper_args__ = {'polymorphic_identity': 'prod'}


class Infra(HostEnvironment):
    __mapper_args__ = {'polymorphic_identity': 'infra'}
