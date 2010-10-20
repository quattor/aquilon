# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
""" Assign Addresses to interfaces """

from datetime import datetime

from sqlalchemy.orm import relation, backref
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey,
                        UniqueConstraint)

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import Base, System, HardwareEntity

_TN = 'primary_name_association'
_ABV = 'primary_name_asc'


class PrimaryNameAssociation(Base):
    """ Assignment of Dns Address Resource Records to network interfaces.

        An essential feature of the overall design is that dns data is kept
        as a discrete set of data that can be isolated and modified independant
        of the machinary that aqd is responsible for configuring. This provides
        maximum flexibility for the future. While it creates a more complex
        design and code (it could be a direct link from the hardware entity
        table), the principle of keeping these data sets loosely coupled is
        considered more important in 2010 after the last few years of developing
        this system.

        It's kept as an association map to model the linkage, since we need to
        have maximum ability to provide potentially complex configuration
        scenarios, such as advertising certain VIP addresses from some, but not
        all of the network interfaces on a machine (to be used for backup
        servers, cluster filesystem servers, NetApp filers, etc.). While in
        most cases we can assume VIPs are broadcast out all interfaces on the
        box we still need to have the underlying model as the more complex
        many to many relationship implemented here.

        Cascade is set up with delete (from all), and delete-orphan such
        that these associations are not to exist without a parent hardware
        entity and deletion of a hardware entity cascades through to the
        ARecord of the hardware
    """
    __tablename__ = _TN

    hardware_entity_id = Column(Integer, ForeignKey('hardware_entity.id',
                                                    name='%s_hw_fk' % _ABV),
                                primary_key=True)

    dns_record_id = Column(Integer, ForeignKey('system.id', ondelete='CASCADE',
                                               name='%s_dns_rec_fk' % _ABV),
                           primary_key=True)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    # Cascading:
    # - do not delete the HW if the association is removed
    # - remove the association if the HW is removed
    hardware_entity = relation(HardwareEntity,
                               lazy=False,
                               uselist=False,
                               innerjoin=True,
                               cascade=False,
                               backref=backref('_primary_name_asc',
                                               uselist=False,
                                               lazy=False,
                                               cascade='all, delete-orphan'))

    # Cascading:
    # - delete the DNS record if the association is removed
    # - delete the association if the DNS record is removed
    dns_record = relation(System,
                          lazy=False,
                          uselist=False,
                          innerjoin=True,
                          cascade='all',
                          backref=backref('_primary_name_asc',
                                          uselist=False,
                                          cascade='all, delete-orphan'))

    def __repr__(self):
        return "<{0} for {1}: {2}>".format(self.__class__.__name__,
                                           self.hardware_entity, self.dns_record)

    #TODO: take fqdn/dns_environment and cut out extra work?
    @classmethod
    def get_unique(cls, sess, dns_record, compel=False, preclude=False):
        """ Take an ARecord, return a PrimaryNameAssociation

            This overridden method is heavily tweaked from the standard
            version supplied to the base class. It seems unlikely we'd run
            into the situation where you have a bit of hardware and need to
            find it's name. It also doesn't support compel and preclude as
            the main use of this method is in HardwareEntity.get_unique, which
            doesn't need the use of these options.
        """
        pna = sess.query(cls).filter_by(dns_record=dns_record).first()
        if not pna and compel:
            raise NotFoundException('No such primary_name assignment %s' % (
                                    dns_record.fqdn))

        if pna and preclude:
            raise ArgumentError('Primary Name %s already exists' % (
                                dns_record.fqdn))

        return pna

pna = PrimaryNameAssociation.__table__  # pylint: disable-msg=C0103

pna.primary_key.name = '%s_pk' % _TN

pna.append_constraint(
    UniqueConstraint('hardware_entity_id', name='%s_hw_ent_uk' % _ABV))

pna.append_constraint(
    UniqueConstraint('dns_record_id', name='%s_dns_uk' % _ABV))


HardwareEntity.primary_name = association_proxy('_primary_name_asc', 'dns_record',
                creator=lambda dns_rec: PrimaryNameAssociation(dns_record=dns_rec))

System.hardware_entity = association_proxy('_primary_name_asc',
                                                  'hardware_entity')
