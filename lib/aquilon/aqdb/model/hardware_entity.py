# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2017,2018  Contributor
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
""" Base class of polymorphic hardware structures """

from datetime import datetime
from inspect import isclass
import re

from sqlalchemy import (Column, Integer, Sequence, ForeignKey, UniqueConstraint,
                        String, DateTime)
from sqlalchemy.orm import relation, backref, lazyload, validates, deferred
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.attributes import set_committed_value

from aquilon.exceptions_ import AquilonError, ArgumentError, NotFoundException
from aquilon.aqdb.model import Base, DnsRecord, Grn, Location, Model
from aquilon.aqdb.column_types import AqStr
from aquilon.config import Config

_TN = "hardware_entity"

_config = Config()


class HardwareEntity(Base):
    __tablename__ = _TN
    _instance_label = 'printable_name'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)

    label = Column(AqStr(63), nullable=False, unique=True)

    hardware_type = Column(AqStr(64), nullable=False)

    location_id = Column(ForeignKey(Location.id), nullable=False, index=True)

    model_id = Column(ForeignKey(Model.id), nullable=False, index=True)

    serial_no = Column(String(64), nullable=True)

    primary_name_id = Column(ForeignKey(DnsRecord.id,
                                        name='%s_pri_name_fk' % _TN),
                             nullable=True)

    owner_eon_id = Column(ForeignKey(Grn.eon_id, name='%s_owner_grn_fk' % _TN),
                          nullable=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    # Most of the update_* commands need to load the comments due to
    # snapshot_hw(), so it is not worth deferring it
    comments = Column(String(255), nullable=True)

    location = relation(Location, innerjoin=True)
    model = relation(Model, innerjoin=True)
    owner_grn = relation(Grn)

    # When working with machines the primary name always crops up, so load it
    # eagerly
    # This is a one-to-one relation, so we need uselist=False on the backref
    primary_name = relation(DnsRecord, lazy=False,
                            backref=backref('hardware_entity', uselist=False,
                                            passive_deletes=True))

    __table_args__ = (UniqueConstraint(primary_name_id,
                                       name='%s_pri_name_uk' % _TN),
                      {'info': {'unique_fields': ['label']}},)
    __mapper_args__ = {'polymorphic_on': hardware_type}

    _label_check = re.compile(_config.get("site", "default_hardware_label_regex"))

    @classmethod
    def check_label(cls, label):
        if not cls._label_check.match(label):
            raise ArgumentError("Illegal hardware label format '%s'. Only "
                                "alphanumeric characters are allowed, and "
                                "the first character must be a letter." % label)

    @validates('label')
    def validate_label(self, key, value):  # pylint: disable=W0613
        self.check_label(value)
        return value

    @validates('location')
    def _validate_location(self, key, value):  # pylint: disable=W0613
        return self.validates_location(key, value)

    def validates_location(self, key, value):
        return value

    def __init__(self, label=None, **kwargs):
        label = AqStr.normalize(label)
        if not label:
            raise AquilonError("HardwareEntity needs a label.")
        super(HardwareEntity, self).__init__(label=label, **kwargs)

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
                                    .format(hwe, clslabel.lower()))
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
                set_committed_value(dns_rec, 'hardware_entity', hwe)

        return hwe

    def all_addresses(self):
        """ Iterator returning all addresses of the hardware. """
        for iface in self.interfaces:
            for addr in iface.assignments:
                yield addr


class DeviceLinkMixin(object):
    _bus_address_checks = {
        # PCI: <domain>:<bus>:<device>.<function>
        'pci': re.compile(r'^[0-9a-f]{4}:[0-9a-f]{2}:[01][0-9a-f]\.[0-7]$')
    }

    bus_address = Column(AqStr(32), nullable=True)

    @validates('bus_address')
    def validate_bus_address(self, key, value):  # pylint: disable=W0613
        if value is None:
            return value

        if ":" not in value:
            raise ValueError("Malformed bus URI specification.")

        # Poor man's URI parser
        scheme, rest = value.split(":", 1)
        if scheme not in self._bus_address_checks:
            raise ValueError("Unknown hardware bus type.")
        if not self._bus_address_checks[scheme].match(rest):
            raise ValueError("Invalid bus address.")

        return value
