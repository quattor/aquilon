# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018-2019  Contributor
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
""" Entitlements management """

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    event,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    Sequence,
    String,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import (
    AbstractConcreteBase,
    declared_attr,
)
from sqlalchemy.orm import (
    deferred,
    object_session,
    relation,
)
from sqlalchemy.sql import and_

from aquilon.aqdb.column_types import AqStr
from aquilon.aqdb.model import (
    Archetype,
    Base,
    Cluster,
    Grn,
    Host,
    HostEnvironment,
    Location,
    Personality,
    User,
    UserType,
)
from aquilon.aqdb.utils.constraints import ref_constraint_name


_TYPES = 'entit_type'
_TYPESUSERMAP = 'entit_type_user_type_map'
_HOSTGRN = 'entit_host_grn_map'
_HOSTUSER = 'entit_host_user_map'
_CLUSTERGRN = 'entit_cluster_grn_map'
_CLUSTERUSER = 'entit_cluster_user_map'
_PERSONALITYGRN = 'entit_personality_grn_map'
_PERSONALITYUSER = 'entit_personality_user_map'
_ARCHETYPEGRN = 'entit_archetype_grn_map'
_ARCHETYPEUSER = 'entit_archetype_user_map'
_GRNGRN = 'entit_grn_grn_map'
_GRNUSER = 'entit_grn_user_map'

_MATCHIDX = 'match'
_GRANTIDX = 'grant'
_IDXSUFFIX = 'idx'


def get_ids(cls, inherit=None):
    """Function that returns all the IDs to use as primary key

    For a given class, this function will check for the _ids parameter and
    call itself recursively on the given class' base classes to append all
    other required IDs, thus generating the list of parameters to use as
    primary key for the database.
    This allows not to repeat the same IDs for each inheritance level and
    to compute it automatically.
    """

    if not inherit or issubclass(cls, inherit):
        ids = list(getattr(cls, '_ids', []))
    else:
        ids = []

    for c in cls.__bases__:
        for i in get_ids(c, inherit):
            if i not in ids:
                ids.append(i)
    return ids


class EntitlementType(Base):
    __tablename__ = _TYPES

    id = Column(Integer, Sequence('%s_id_seq' % __tablename__),
                primary_key=True)
    name = Column(AqStr(64), nullable=False, unique=True)

    # Boolean to indicate if the entitlement type allows to set entitlement
    # to GRNs or not
    to_grn = Column(Boolean, nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = Column(String(255), nullable=True)

    __table_args__ = ({'info': {'unique_fields': ['name']}},)


class EntitlementTypeUserTypeMap(Base):
    __tablename__ = _TYPESUSERMAP

    entitlement_type_id = Column(ForeignKey(EntitlementType.id,
                                            ondelete='CASCADE'),
                                 nullable=False)
    entitlement_type = relation(EntitlementType, lazy=False, innerjoin=True)

    user_type_id = Column(ForeignKey(UserType.id, ondelete='CASCADE'),
                          nullable=False)
    user_type = relation(UserType, lazy=False, innerjoin=True)

    __table_args__ = (
        PrimaryKeyConstraint(entitlement_type_id, user_type_id),
        Index(ref_constraint_name(local_table=__tablename__,
                                  column='enttyp',
                                  suffix=_IDXSUFFIX),
              entitlement_type_id),
        Index(ref_constraint_name(local_table=__tablename__,
                                  column='usrtyp',
                                  suffix=_IDXSUFFIX),
              user_type_id),
    )


# List of user types an entitlement type allows to set entitlements to
EntitlementType.to_user_types = relation(EntitlementTypeUserTypeMap,
                                         cascade='all, delete-orphan',
                                         passive_deletes=True)


class EntitlementId(Base):
    """Entitlement identificator table to be used as foreign key

    This table is mainly useful to reference an unique and primary key
    for all entitlement, including all entitlement classes. This allows
    to reference entitlements by using a unique foreign key instead of
    having to repeat all entitlements specifics like the object on which
    it applies (and all parameters such as the location and environment)
    and the object to which it applies.
    """
    __tablename__ = 'entitlement'
    id = Column(Integer, Sequence('%s_id_seq' % __tablename__),
                primary_key=True)

    @property
    def entitlement(self):
        """Property to return the entitlement corresponding to that id"""
        session = object_session(self)

        q = session.query(Entitlement)
        q = q.filter_by(id=self.id)

        return q.one()


class Entitlement(AbstractConcreteBase, Base):
    """Base class of all entitlements

    It represents a low level entitlement, on top of which all entitlements
    will be built. It provides the wrapper functions/attributes that apply
    to all entitlements.

    The entitlements are structured in different tables, and each entitlement
    with its own specific 'to' and 'on' parameters will be different than the
    others and have its own class (and thus, database table). This will allow
    for a clearer and easier way to query and search entitlements, as well as
    for normalized tables representing the entitlements.
    """

    @declared_attr
    def __mapper_args__(cls):
        if not hasattr(cls, '__tablename__'):
            return {}

        return {
            'polymorphic_identity': cls.__name__,
            'concrete': True,
        }

    @declared_attr
    def __table_args__(cls):
        if not hasattr(cls, '__tablename__'):
            return ()

        return (
            UniqueConstraint(*get_ids(cls),
                             name='{}_uk'.format(cls.__tablename__)),
            Index(ref_constraint_name(local_table=cls.__tablename__,
                                      column=_MATCHIDX,
                                      suffix=_IDXSUFFIX),
                  *get_ids(cls, EntitlementOn)),
            Index(ref_constraint_name(local_table=cls.__tablename__,
                                      column=_GRANTIDX,
                                      suffix=_IDXSUFFIX),
                  *get_ids(cls, EntitlementTo))
        )

    @property
    def hostlinks(self):
        """Property to return the hostlinks related to the entitlement"""
        # Avoid circular dependency
        from aquilon.aqdb.model import (
            Hostlink,
            HostlinkEntitlementMap,
        )

        session = object_session(self)
        q = session.query(Hostlink)
        q = q.join(HostlinkEntitlementMap, and_(
            HostlinkEntitlementMap.resource_id == Hostlink.resource_id,
            HostlinkEntitlementMap.entitlement_id == self.id))

        return q.all()


class EntitlementWithId(object):
    """Base class for the id of the Entitlement

    It allows to add an id parameter on the inherited classes. This is
    separate from the Entitlement class because of the way sqlalchemy work
    for abstractly inherited classes that build SQL tables.

    The id parameter is a foreign key related to the EntitlementId class,
    which provides a unique id for all entitlements, and can be used as
    a foreign key to reference an entitlement in any other table.
    The idobj parameter returns the EntitlementId object.
    """

    @declared_attr
    def id(cls):
        return Column(ForeignKey(EntitlementId.id, ondelete='CASCADE',
                                 name=ref_constraint_name(
                                    local_table=cls.__tablename__,
                                    column='id',
                                    suffix='fk')),
                      nullable=False, primary_key=True)

    @declared_attr
    def idobj(cls):
        return relation(EntitlementId, lazy=False, innerjoin=True,
                        foreign_keys=cls.id)


class EntitlementWithType(object):
    """Base class for the type of the Entitlement

    It allows to add a type parameter on the inherited classes. This is
    separate from the Entitlement class because of the way sqlalchemy work
    for abstractly inherited classes that build SQL tables.
    """

    @declared_attr
    def type_id(cls):
        return Column(ForeignKey(EntitlementType.id,
                                 name=ref_constraint_name(
                                    local_table=cls.__tablename__,
                                    column='type',
                                    suffix='fk')),
                      nullable=False)

    @declared_attr
    def type(cls):
        return relation(EntitlementType, lazy=False, innerjoin=True,
                        foreign_keys=cls.type_id)

    _ids = ('type_id', )


class EntitlementTo(object):
    """Base class for the 'to' part of the Entitlement

    It has to be inherited by any class that wants to specify the 'to'
    part of an Entitlement (who/what we are entitling to)
    """
    pass


class EntitlementToUser(EntitlementTo):
    """Base class for entitlements to a User

    It has to be inherited by any table allowing to entitle to a User
    """

    @declared_attr
    def user_id(cls):
        return Column(ForeignKey(User.id, ondelete='CASCADE'), nullable=False)

    @declared_attr
    def user(cls):
        return relation(User, lazy=False, innerjoin=True,
                        foreign_keys=cls.user_id)

    _ids = ('user_id', )
    _to_class = User


class EntitlementToGrn(EntitlementTo):
    """Base class for entitlements to a Grn

    It has to be inherited by any table allowing to entitle to a Grn
    """

    @declared_attr
    def eon_id(cls):
        return Column(ForeignKey(Grn.eon_id, ondelete='CASCADE'),
                      nullable=False)

    @declared_attr
    def grn(cls):
        return relation(Grn, lazy=False, innerjoin=True,
                        foreign_keys=cls.eon_id)

    _ids = ('eon_id', )
    _to_class = Grn


class EntitlementOn(object):
    """Base class for the 'on' part of the Entitlement

    It has to be inherited by any class that wants to specify the 'on'
    part of an Entitlement (what we are entitling on)
    """
    pass


class EntitlementOnHost(EntitlementOn):
    """Base class for entitlements on a Host

    It has to be inherited by any table allowing to entitle on a Host
    """

    @declared_attr
    def host_id(cls):
        return Column(ForeignKey(Host.hardware_entity_id, ondelete="CASCADE"),
                      nullable=False)

    @declared_attr
    def host(cls):
        return relation(Host, lazy=False, innerjoin=True,
                        foreign_keys=cls.host_id)

    _ids = ('host_id', )
    _on_class = Host


class EntitlementOnCluster(EntitlementOn):
    """Base class for entitlements on a Cluster

    It has to be inherited by any table allowing to entitle on a Cluster
    """

    @declared_attr
    def cluster_id(cls):
        return Column(ForeignKey(Cluster.id, ondelete="CASCADE"),
                      nullable=False)

    @declared_attr
    def cluster(cls):
        return relation(Cluster, lazy=False, innerjoin=True,
                        foreign_keys=cls.cluster_id)

    _ids = ('cluster_id', )
    _on_class = Cluster


class EntitlementOnLocation(EntitlementOn):
    """Base class for entitlements on a Location

    It has to be inherited by any table allowing to entitle on a Location
    """

    @declared_attr
    def location_id(cls):
        return Column(ForeignKey(Location.id, ondelete='CASCADE'),
                      nullable=False)

    @declared_attr
    def location(cls):
        return relation(Location, lazy=False, innerjoin=True,
                        foreign_keys=cls.location_id)

    _ids = ('location_id', )


class EntitlementOnHostEnvironment(EntitlementOn):
    """Base class for entitlements on a Host Environment

    It has to be inherited by any table allowing to entitle on a Host
    Environment
    """

    @declared_attr
    def host_environment_id(cls):
        return Column(ForeignKey(HostEnvironment.id, ondelete='CASCADE'),
                      nullable=False)

    @declared_attr
    def host_environment(cls):
        return relation(HostEnvironment, lazy=False, innerjoin=True,
                        foreign_keys=cls.host_environment_id)

    _ids = ('host_environment_id', )


class EntitlementOnPersonality(EntitlementOnLocation):
    """Base class for entitlements on a Personality

    It has to be inherited by any table allowing to entitle on a
    Personality; it includes the EntitlementOnLocation class to be able
    to limit the application of that Entitlement to a given Location in
    addition to the Personality.
    """

    @declared_attr
    def personality_id(cls):
        return Column(ForeignKey(Personality.id, ondelete='CASCADE'),
                      nullable=False)

    @declared_attr
    def personality(cls):
        return relation(Personality, lazy=False, innerjoin=True,
                        foreign_keys=cls.personality_id)

    _ids = ('personality_id', )
    _on_class = Personality


class EntitlementOnArchetype(EntitlementOnHostEnvironment,
                             EntitlementOnLocation):
    """Base class for entitlements on an architecture type

    It has to be inherited by any table allowing to entitle on an
    architecture type; it includes the EntitlementOnLocation and
    EntitlementOnHostEnvironment classes to be able to limit the
    application of that Entitlement to a given Location and
    Host Environment in addition to the Archetype.
    """

    @declared_attr
    def archetype_id(cls):
        return Column(ForeignKey(Archetype.id, ondelete='CASCADE'),
                      nullable=False)

    @declared_attr
    def archetype(cls):
        return relation(Archetype, lazy=False, innerjoin=True,
                        foreign_keys=cls.archetype_id)

    _ids = ('archetype_id', )
    _on_class = Archetype


class EntitlementOnGrn(EntitlementOnHostEnvironment,
                       EntitlementOnLocation):
    """Base class for entitlements on a Grn

    It has to be inherited by any table allowing to entitle on a Grn;
    it includes the EntitlementOnLocation and EntitlementOnHostEnvironment
    classes to be able to limit the application of that Entitlement to
    a given Location and Host Environment in addition to the Grn.
    """

    @declared_attr
    def target_eon_id(cls):
        return Column(ForeignKey(Grn.eon_id, ondelete='CASCADE',
                                 name=ref_constraint_name(
                                    local_table=cls.__tablename__,
                                    column='target_grn',
                                    suffix='fk')),
                      nullable=False)

    @declared_attr
    def target_grn(cls):
        return relation(Grn, lazy=False, innerjoin=True,
                        foreign_keys=cls.target_eon_id)

    _ids = ('target_eon_id', )
    _on_class = Grn


class EntitlementHostGrnMap(EntitlementWithId,
                            EntitlementWithType,
                            EntitlementOnHost,
                            EntitlementToGrn,
                            Entitlement):
    """Class to represent the table that entitles to a Grn on a Host"""
    __tablename__ = _HOSTGRN

    def __init__(self, *args, **kwargs):
        if 'id' not in kwargs and 'idobj' not in kwargs:
            kwargs['idobj'] = EntitlementId()
        super(EntitlementHostGrnMap, self).__init__(*args, **kwargs)


class EntitlementHostUserMap(EntitlementWithId,
                             EntitlementWithType,
                             EntitlementOnHost,
                             EntitlementToUser,
                             Entitlement):
    """Class to represent the table that entitles to a User on a Host"""
    __tablename__ = _HOSTUSER

    def __init__(self, *args, **kwargs):
        if 'id' not in kwargs and 'idobj' not in kwargs:
            kwargs['idobj'] = EntitlementId()
        super(EntitlementHostUserMap, self).__init__(*args, **kwargs)


Host.entitled_grns = relation(EntitlementHostGrnMap,
                              cascade='all, delete-orphan',
                              passive_deletes=True)
Host.entitled_users = relation(EntitlementHostUserMap,
                               cascade='all, delete-orphan',
                               passive_deletes=True)


class EntitlementClusterGrnMap(EntitlementWithId,
                               EntitlementWithType,
                               EntitlementOnCluster,
                               EntitlementToGrn,
                               Entitlement):
    """Class to represent the table that entitles to a Grn on a Cluster"""
    __tablename__ = _CLUSTERGRN

    def __init__(self, *args, **kwargs):
        if 'id' not in kwargs and 'idobj' not in kwargs:
            kwargs['idobj'] = EntitlementId()
        super(EntitlementClusterGrnMap, self).__init__(*args, **kwargs)


class EntitlementClusterUserMap(EntitlementWithId,
                                EntitlementWithType,
                                EntitlementOnCluster,
                                EntitlementToUser,
                                Entitlement):
    """Class to represent the table that entitles to a User on a Cluster"""
    __tablename__ = _CLUSTERUSER

    def __init__(self, *args, **kwargs):
        if 'id' not in kwargs and 'idobj' not in kwargs:
            kwargs['idobj'] = EntitlementId()
        super(EntitlementClusterUserMap, self).__init__(*args, **kwargs)


Cluster.entitled_grns = relation(EntitlementClusterGrnMap,
                                 cascade='all, delete-orphan',
                                 passive_deletes=True)
Cluster.entitled_users = relation(EntitlementClusterUserMap,
                                  cascade='all, delete-orphan',
                                  passive_deletes=True)


class EntitlementPersonalityGrnMap(EntitlementWithId,
                                   EntitlementWithType,
                                   EntitlementOnPersonality,
                                   EntitlementToGrn,
                                   Entitlement):
    """Class to represent the table that entitles to a Grn on a Personality"""
    __tablename__ = _PERSONALITYGRN

    def __init__(self, *args, **kwargs):
        if 'id' not in kwargs and 'idobj' not in kwargs:
            kwargs['idobj'] = EntitlementId()
        super(EntitlementPersonalityGrnMap, self).__init__(*args, **kwargs)


class EntitlementPersonalityUserMap(EntitlementWithId,
                                    EntitlementWithType,
                                    EntitlementOnPersonality,
                                    EntitlementToUser,
                                    Entitlement):
    """Class to represent the table that entitles to a User on a Personality"""
    __tablename__ = _PERSONALITYUSER

    def __init__(self, *args, **kwargs):
        if 'id' not in kwargs and 'idobj' not in kwargs:
            kwargs['idobj'] = EntitlementId()
        super(EntitlementPersonalityUserMap, self).__init__(*args, **kwargs)


Personality.entitled_grns = relation(EntitlementPersonalityGrnMap,
                                     cascade='all, delete-orphan',
                                     passive_deletes=True)
Personality.entitled_users = relation(EntitlementPersonalityUserMap,
                                      cascade='all, delete-orphan',
                                      passive_deletes=True)


class EntitlementArchetypeGrnMap(EntitlementWithId,
                                 EntitlementWithType,
                                 EntitlementOnArchetype,
                                 EntitlementToGrn,
                                 Entitlement):
    """Class to represent the table that entitles to a Grn on an Archetype"""
    __tablename__ = _ARCHETYPEGRN

    def __init__(self, *args, **kwargs):
        if 'id' not in kwargs and 'idobj' not in kwargs:
            kwargs['idobj'] = EntitlementId()
        super(EntitlementArchetypeGrnMap, self).__init__(*args, **kwargs)


class EntitlementArchetypeUserMap(EntitlementWithId,
                                  EntitlementWithType,
                                  EntitlementOnArchetype,
                                  EntitlementToUser,
                                  Entitlement):
    """Class to represent the table that entitles to a User on an Archetype"""
    __tablename__ = _ARCHETYPEUSER

    def __init__(self, *args, **kwargs):
        if 'id' not in kwargs and 'idobj' not in kwargs:
            kwargs['idobj'] = EntitlementId()
        super(EntitlementArchetypeUserMap, self).__init__(*args, **kwargs)


Archetype.entitled_grns = relation(EntitlementArchetypeGrnMap,
                                   cascade='all, delete-orphan',
                                   passive_deletes=True)
Archetype.entitled_users = relation(EntitlementArchetypeUserMap,
                                    cascade='all, delete-orphan',
                                    passive_deletes=True)


class EntitlementGrnGrnMap(EntitlementWithId,
                           EntitlementWithType,
                           EntitlementOnGrn,
                           EntitlementToGrn,
                           Entitlement):
    """Class to represent the table that entitles to a Grn on a Grn"""
    __tablename__ = _GRNGRN

    def __init__(self, *args, **kwargs):
        if 'id' not in kwargs and 'idobj' not in kwargs:
            kwargs['idobj'] = EntitlementId()
        super(EntitlementGrnGrnMap, self).__init__(*args, **kwargs)


class EntitlementGrnUserMap(EntitlementWithId,
                            EntitlementWithType,
                            EntitlementOnGrn,
                            EntitlementToUser,
                            Entitlement):
    """Class to represent the table that entitles to a User on a Grn"""
    __tablename__ = _GRNUSER

    def __init__(self, *args, **kwargs):
        if 'id' not in kwargs and 'idobj' not in kwargs:
            kwargs['idobj'] = EntitlementId()
        super(EntitlementGrnUserMap, self).__init__(*args, **kwargs)


Grn.entitled_grns = relation(EntitlementGrnGrnMap,
                             cascade='all, delete-orphan',
                             passive_deletes=True,
                             foreign_keys=EntitlementGrnGrnMap.target_eon_id)
Grn.entitled_users = relation(EntitlementGrnUserMap,
                              cascade='all, delete-orphan',
                              passive_deletes=True)


def receive_after_delete_entitlement(mapper, connection, target):
    """Function to be run after we received a delete for an entitlement

    This is used to take care of the cleanup needed after removing an
    entitlement; for instance, an entitlement id entry is added when
    creating a new entitlement, and this is used to remove that entry
    from the entitlement table as well as from the specific per-on
    and per-to entitlement (e.g. on host/to user) when the later is
    being deleted.
    """
    # Create a new session to make the change
    session = object_session(target).__class__(bind=connection)

    # Query for the EntitlementId entry that corresponds to that id,
    # and delete it
    session.query(EntitlementId).filter_by(id=target.id).delete()

    # Commit the changes
    session.commit()


# This goes through all the entitlement subclasses and declare the
# after_delete event on each of them
for cls in Entitlement.__subclasses__():
    event.listen(cls, 'after_delete', receive_after_delete_entitlement)
