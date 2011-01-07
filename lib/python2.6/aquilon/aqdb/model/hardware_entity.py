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
""" Base class of polymorphic hardware structures """

from datetime import datetime
from inspect import isclass
import re

from sqlalchemy import (Column, Integer, Sequence, ForeignKey, UniqueConstraint,
                        Index, String, DateTime)
from sqlalchemy.orm import relation

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import Base, Location, Model, DnsRecord
from aquilon.aqdb.column_types import AqStr, Enum

HARDWARE_TYPES = ['machine', 'switch', 'chassis']  # , 'netapp_filer']
_TN = "hardware_entity"


class HardwareEntity(Base):  # pylint: disable-msg=W0232, R0903
    __tablename__ = _TN
    _instance_label = 'printable_name'

    id = Column(Integer, Sequence('%s_seq' % _TN), primary_key=True)

    label = Column(AqStr(63), nullable=False)

    hardware_type = Column(Enum(64, HARDWARE_TYPES), nullable=False)

    location_id = Column(Integer, ForeignKey('location.id',
                                            name='hw_ent_loc_fk'),
                         nullable=False)

    model_id = Column(Integer, ForeignKey('model.id',
                                          name='hw_ent_model_fk'),
                      nullable=False)

    serial_no = Column(String(64), nullable=True)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    location = relation(Location, uselist=False)
    model = relation(Model, uselist=False)

    __mapper_args__ = {'polymorphic_on': hardware_type}

    _label_check = re.compile("^[a-z][a-z0-9]{,62}$")

    @classmethod
    def valid_label(cls, label):
        return cls._label_check.match(label)

    def __init__(self, label=None, **kwargs):
        if not label:
            raise ArgumentError("HardwareEntity needs a label.")
        elif not self.valid_label(label):
            raise ArgumentError("Illegal hardware label format '%s'. Only "
                                "alphanumeric characters are allowed." % label)
        super(HardwareEntity, self).__init__(label=label, **kwargs)

    @property
    def fqdn(self):
        """ Returns the FQDN, if there is a primary name """
        if self.primary_name:
            return self.primary_name.fqdn
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
            return self.primary_name.fqdn
        else:
            return self.label

    @classmethod
    def get_unique(cls, sess, name, **kw):
        """ Returns a unique HardwareEntity given session and fqdn """
        import aquilon.aqdb.model.primary_name_association as pna
        # Using a series of get_unique's under the covers may be inefficient
        # the aim is to get functional code as quick as possible for now.
        # The import required at runtime due to circular dependency between
        # PrimaryNameAssociation and HardwareEntity.

        compel = kw.pop('compel', False)
        preclude = kw.pop('preclude', False)
        hardware_type = kw.pop('hardware_type', None)

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

        hwe = None

        if "." in name:
            dns_rec = DnsRecord.get_unique(sess, fqdn=name)
            my_pna = pna.PrimaryNameAssociation.get_unique(sess, dns_rec)
            if my_pna:
                hwe = my_pna.hardware_entity
        else:
            # Always do the query against the base class, so we can detect
            # hardware_type mismatches
            hwe = sess.query(HardwareEntity).filter_by(label=name).first()

        if hwe:
            if hardware_type and hwe.hardware_type != hardware_type:
                msg = "{0} exists, but is not a {1}.".format(hwe, hardware_type)
                raise ArgumentError(msg)
            if preclude:
                raise ArgumentError('{0} already exists.'.format(hwe))
            else:
                return hwe

        if compel and not hwe:
            msg = "%s %s not found." % (clslabel, name)
            raise NotFoundException(msg)
        else:
            return None

    #Pseudosql for a full sql query implementation for get_unique:
    #select the hardware_entity from the primary_name_association of:
        #select the primary_name_association with an a_record with the id of:
            #select the dns_record with name, domain name
                #select the dns_domain_id with the name of 'domain_name

    def all_addresses(self):
        """ Iterator returning all addresses of the hardware. """
        for iface in self.interfaces:
            for addr in iface.assignments:
                yield addr


hardware_entity = HardwareEntity.__table__
hardware_entity.primary_key.name = '%s_pk' % _TN
hardware_entity.append_constraint(UniqueConstraint('label', name='%s_label_uk' % _TN))
hardware_entity.info['unique_fields'] = ['label']
Index('hw_ent_loc_idx',  hardware_entity.c.location_id)
