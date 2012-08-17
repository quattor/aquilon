# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
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
""" Base class of polymorphic hardware structures """

from datetime import datetime
from inspect import isclass
import re

from sqlalchemy import (Column, Integer, Sequence, ForeignKey, UniqueConstraint,
                        Index, String, DateTime)
from sqlalchemy.orm import relation, backref, lazyload, validates, deferred
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.attributes import set_committed_value

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import Base, Location, Model, DnsRecord
from aquilon.aqdb.column_types import AqStr

_TN = "hardware_entity"


class HardwareEntity(Base):
    __tablename__ = _TN
    _instance_label = 'printable_name'

    id = Column(Integer, Sequence('%s_seq' % _TN), primary_key=True)

    label = Column(AqStr(63), nullable=False)

    hardware_type = Column(AqStr(64), nullable=False)

    location_id = Column(Integer, ForeignKey('location.id',
                                            name='hw_ent_loc_fk'),
                         nullable=False)

    model_id = Column(Integer, ForeignKey('model.id',
                                          name='hw_ent_model_fk'),
                      nullable=False)

    serial_no = Column(String(64), nullable=True)

    primary_name_id = Column(Integer, ForeignKey('dns_record.id',
                                                 name='hw_ent_pri_name_fk'),
                             nullable=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = Column(String(255), nullable=True)

    location = relation(Location)
    model = relation(Model)

    # When working with machines the primary name always crops up, so load it
    # eagerly
    # This is a one-to-one relation, so we need uselist=False on the backref
    primary_name = relation(DnsRecord, lazy=False,
                            backref=backref('hardware_entity', uselist=False))

    __mapper_args__ = {'polymorphic_on': hardware_type}

    _label_check = re.compile("^[a-z][a-z0-9]{,62}$")

    @classmethod
    def check_label(cls, label):
        if not cls._label_check.match(label):
            raise ArgumentError("Illegal hardware label format '%s'. Only "
                                "alphanumeric characters are allowed, and "
                                "the first character must be a letter." % label)

    @validates('label')
    def validate_label(self, key, value):
        self.check_label(value)
        return value

    def __init__(self, label=None, **kwargs):
        label = AqStr.normalize(label)
        if not label:
            raise ArgumentError("HardwareEntity needs a label.")
        super(HardwareEntity, self).__init__(label=label, **kwargs)

    def __lt__(self, other):
        return self.label < other.label

    @property
    def fqdn(self):
        """ Returns the FQDN, if there is a primary name """
        if self.primary_name:
            return str(self.primary_name.fqdn)
        else:
            return None

    @property
    def primary_ip(self):
        """ Returns the primary IP, if there is one """
        if self.primary_name and hasattr(self.primary_name, "ip"):
            return self.primary_name.ip
        else:
            return None

    @property
    def printable_name(self):
        """ Returns the most meaningful name """
        if self.primary_name:
            return str(self.primary_name.fqdn)
        else:
            return self.label

    @classmethod
    def get_unique(cls, sess, name, hardware_type=None, compel=False,
                   preclude=False, query_options=None):
        """ Returns a unique HardwareEntity given session and fqdn """

        # If the hardware_type param isn't explicitly set and we have a
        # polymorphic identity, assume we're querying only for items of our
        # hardware_type.
        if hardware_type:
            if isclass(hardware_type):
                clslabel = hardware_type._get_class_label()
                hardware_type = hardware_type.__mapper_args__['polymorphic_identity']
            else:
                pcls = cls.__mapper__.polymorphic_map[hardware_type].class_
                clslabel = pcls._get_class_label()
        else:
            if 'polymorphic_identity' in cls.__mapper_args__:
                hardware_type = cls.__mapper_args__['polymorphic_identity']
            clslabel = cls._get_class_label()

        # The automagic DNS lookup does not really make sense with preclude=True
        if preclude:
            name = AqStr.normalize(name)
            cls.check_label(name)

        q = sess.query(cls)
        if "." in name:
            dns_rec = DnsRecord.get_unique(sess, fqdn=name, compel=True)
            # We know the primary name, do not load it again
            q = q.options(lazyload('primary_name'))
            q = q.filter_by(primary_name=dns_rec)
        else:
            dns_rec = None
            q = q.filter_by(label=name)
        if query_options:
            q = q.options(*query_options)

        try:
            hwe = q.one()
        except NoResultFound:
            # Check if the name is in use by a different hardware type
            q = sess.query(HardwareEntity)
            if dns_rec:
                # We know the primary name, do not load it again
                q = q.options(lazyload('primary_name'))
                q = q.filter_by(primary_name=dns_rec)
            else:
                q = q.filter_by(label=name)
            try:
                hwe = q.one()
                if dns_rec:
                    # We know the primary name, do not load it again
                    set_committed_value(hwe, 'primary_name', dns_rec)
                raise ArgumentError("{0} exists, but is not a {1}."
                                    .format(hwe, hardware_type))
            except NoResultFound:
                hwe = None

            if compel:
                raise NotFoundException("%s %s not found." % (clslabel, name))

        if hwe:
            if preclude:
                raise ArgumentError('{0} already exists.'.format(hwe))
            if dns_rec:
                # We know the primary name, do not load it again
                set_committed_value(hwe, 'primary_name', dns_rec)

        return hwe

    def all_addresses(self):
        """ Iterator returning all addresses of the hardware. """
        for iface in self.interfaces:
            for addr in iface.assignments:
                yield addr


hardware_entity = HardwareEntity.__table__  # pylint: disable=C0103
hardware_entity.primary_key.name = '%s_pk' % _TN
hardware_entity.append_constraint(UniqueConstraint('label', name='%s_label_uk' % _TN))
hardware_entity.info['unique_fields'] = ['label']
Index('hw_ent_loc_idx', hardware_entity.c.location_id)
