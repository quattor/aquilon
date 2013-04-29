# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
import sys

from inspect import isclass

from sqlalchemy.schema import CreateTable
from sqlalchemy.orm.session import Session, object_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm.properties import RelationProperty, ColumnProperty
from sqlalchemy.ext.associationproxy import AssociationProxy, _lazy_collection
from sqlalchemy.inspection import inspect

from aquilon.utils import monkeypatch
from aquilon.exceptions_ import InternalError, NotFoundException, ArgumentError


def _raise_custom(cls, defcls, msg):
    if isclass(cls) and issubclass(cls, Exception):
        raise cls(msg)
    else:
        raise defcls(msg)


class Base(object):
    """ The abstract base class for all aqdb objects """

    def __init__(self, **kw):
        for k in kw:
            if not hasattr(type(self), k):  # pragma: no cover
                msg = "%r is an invalid argument for %s" % (
                    k, type(self).__name__)
                raise TypeError(msg)
            setattr(self, k, kw[k])

    def __repr__(self):
        """
        Return an internal representation of the object.

        This representation is intended mainly for debugging, and it should
        uniquely identify the instance. The output of repr() should never be
        sent to the client, and should only appear in server-side logs at the
        debug level.
        """
        label = self.__class__.__name__
        attrs = []
        mapper = inspect(self.__class__)
        for field, prop in mapper.column_attrs.items():
            # Do not load deferred columns, they can't be that interesting
            if prop.deferred:
                continue

            # Skip the column holding the polymorphic identity, since the
            # information is already present in the class name
            if mapper.polymorphic_on is not None and \
               mapper.polymorphic_on.name == field:
                continue

            # These fields are not really interesting
            if field == 'id' or field == 'creation_date' or field == 'comments':
                continue

            # Convert foreign IDs to names
            if field.endswith("_id") and field[:-3] in mapper.relationships:
                field = field[:-3]
            value = getattr(self, field, None)

            attrs.append("%s: %s" % (field, value))
        return "<%s %s>" % (label, ", ".join(attrs))

    def __str__(self):
        """
        Return the most significant attribute of the object.

        If the object has a single field that makes it unique, then that field
        should be returned.
        """
        return str(self._get_instance_label())

    def format_helper(self, format_spec, instance):
        """ Common helper for formatting functions """
        lowercase = False
        class_only = False
        passthrough = ""
        for letter in format_spec:
            if letter == "l":
                lowercase = True
            elif letter == "c":
                class_only = True
            else:
                passthrough += letter

        clsname = self.__class__._get_class_label(tolower=lowercase)
        if class_only:
            return clsname.__format__(passthrough)
        val = "%s %s" % (clsname, instance)
        return val.__format__(passthrough)

    def __format__(self, format_spec):
        """
        Return a pretty-printed representation of the object.

        The output of format() should be the preferred form when referring to
        this object in messages sent to the client. It should be readable as
        plain text, and should uniquely identify the object.

        The format_spec argument can be a standard format specifier suitable for
        strings, with some extensions:

        - specifying the 'l' flag will format the class label in lower case,
          except abbreviations.

        - specifying the 'c' flag will return the pretty printed class name
        """

        return self.format_helper(format_spec, self._get_instance_label())

    @classmethod
    def _get_class_label(cls, tolower=False):
        label = getattr(cls, "_class_label", cls.__name__)
        if tolower:
            parts = label.split()
            # 'Operating System' -> 'operating system', but:
            # 'ESX Cluster' -> 'ESX cluster'
            # 'ToR Switch' -> 'ToR switch'
            #
            # Heuristic: a word is an acronym if the last letter is in upper
            # case
            label = ' '.join(map(lambda x: x if x[:-1].isupper() else x.lower(), parts))
        return label

    def _get_instance_label(self):
        """ Subclasses can override this method or just set a property to check

            If an instance has an attribute named _instance_label, the property
            named by that attribute will be checked for an identifier.

            Without _instance_label set, the properties 'name' and 'type' are
            checked, followed by service.name and system.name.

            For situations more complex than just checking a property this
            method should be overridden with the necessary logic.
        """
        if hasattr(self, "_instance_label"):
            return getattr(self, getattr(self, "_instance_label"))
        for attr in ['name', 'type']:
            if hasattr(self, attr):
                return getattr(self, attr)
        # These might not be necessary any more...
        for attr in ['service', 'system']:
            if hasattr(self, attr):
                return getattr(self, attr).name
        return 'instance'

    @classmethod
    def _selection_helper(cls, session, query, *args, **kwargs):
        """ Helper method for get_unique and get_matching_ids

            Every class that wishes to support get_unique() must have
            'unique_fields' defined in the table's info dictionary.
            'unique_fields' is a list that contains the names of fields that
            make the object unique. Every field can be either a column or a
            relation. In the latter case, 'unique_fields' of the referenced
            class must contain a single field only
        """

        compel = kwargs.pop('compel', False)
        table = cls.__table__
        mapper = inspect(cls)
        caller = sys._getframe(1).f_code.co_name
        clslabel = cls._get_class_label()

        if not isinstance(session, Session):  # pragma: no cover
            raise TypeError("The first argument of %s() must be an "
                            "SQLAlchemy session." % caller)

        if 'unique_fields' not in table.info:
            raise InternalError("Class %s is not annotated to be used with "
                                "%s()." % (cls.__name__, caller))

        # Handle positional arguments
        if args:
            if len(args) > 1:
                raise InternalError("%s() does not support multiple positional"
                                    "arguments, use named arguments." % caller)
            if len(table.info['unique_fields']) > 1:
                raise InternalError("The uniqueness criteria for class %s "
                                    "includes multiple fields, positional "
                                    "arguments cannot be used." % cls.__name__)
            if kwargs:
                raise InternalError("Cannot mix positional and named "
                                    "arguments with %s()." % caller)
            kwargs = {table.info['unique_fields'][0]: args[0]}

        desc = []
        # We don't want to modify the table description below, so make a copy
        fields = table.info['unique_fields'][:]
        if 'extra_search_fields' in table.info:
            fields.extend(table.info['extra_search_fields'])
        for field in fields:
            value = kwargs.pop(field, None)
            if value is None:
                continue

            # Do a lookup if the field refers to a relation but the argument
            # given is not a DB object
            if field in mapper.relationships:
                rel = mapper.relationships[field]
                if not isinstance(value, rel.argument):
                    value = rel.argument.get_unique(session, value,
                                                    compel=compel)

            # filter_by() would be simpler but it would not allow querying just
            # one column
            query = query.filter(getattr(cls, field) == value)

            # Now some beautification...
            poly_column = mapper.polymorphic_on
            if poly_column is not None and poly_column.name == field:
                # Return "Building foo" instead of "Location foo, location_type
                # building"
                clslabel = mapper.polymorphic_map[value].class_._get_class_label()
            else:
                if field == "name" or (hasattr(cls, "_instance_label") and
                                       field == cls._instance_label):  # pylint: disable=E1101
                    desc.insert(0, str(value))
                elif isinstance(value, Base):
                    desc.append("{0:l}".format(value))
                else:
                    desc.append(field + " " + str(value))

        # Check for arguments we don't know about
        if kwargs:
            raise InternalError("Class %s: Extra arguments to %s(): %s." %
                                (cls.__name__, caller, kwargs))
        return (query, clslabel, desc)

    @classmethod
    def get_unique(cls, session, *args, **kwargs):
        compel = kwargs.get('compel', False)
        preclude = kwargs.pop('preclude', False)
        options = kwargs.pop('query_options', None)

        query = session.query(cls)
        if options:
            query = query.options(*options)
        (query, clslabel, desc) = cls._selection_helper(session, query, *args,
                                                        **kwargs)
        try:
            obj = query.one()
            if preclude:
                # The object may belong to a subclass of what was requested, so
                # query its class label instead of using the precomputed value
                msg = "%s %s already exists." % (obj._get_class_label(),
                                                 ", ".join(desc))
                _raise_custom(preclude, ArgumentError, msg)
            return obj
        except NoResultFound:
            if not compel:
                return None
            msg = "%s %s not found." % (clslabel, ", ".join(desc))
            _raise_custom(compel, NotFoundException, msg)
        except MultipleResultsFound:
            msg = "%s %s is not unique." % (clslabel, ", ".join(desc))
            raise ArgumentError(msg)

    @classmethod
    def get_matching_query(cls, session, *args, **kwargs):
        compel = kwargs.get('compel', False)
        options = kwargs.pop('query_options', None)

        query = session.query(cls.__table__.c.id)
        if options:
            query = query.options(*options)
        (query, clslabel, desc) = cls._selection_helper(session, query, *args,
                                                        **kwargs)
        if compel:
            obj = query.first()
            if obj is None:
                msg = "%s %s not found." % (clslabel, ", ".join(desc))
                _raise_custom(compel, NotFoundException, msg)
        return query.subquery()

    def lock_row(self):
        """
        Lock an object in the database.

        The function works by issuing a SELECT ... FOR UPDATE query.
        """

        session = object_session(self)
        if not session:  # pragma: no cover
            raise InternalError("lock_row() called on a detached object %r" %
                                self)

        pk = inspect(self).mapper.primary_key
        q = session.query(*pk)
        for col in pk:
            q = q.filter(col == getattr(self, col.key))

        q = q.with_lockmode("update")
        return q.one()

    @classmethod
    def polymorphic_subclass(cls, value, msg, error=ArgumentError):
        value = value.strip().lower()
        mapper = inspect(cls)
        if value not in mapper.polymorphic_map.keys():
            valid_values = ", ".join(sorted(mapper.polymorphic_map.keys()))
            raise error("%s '%s'. The valid values are: %s." %
                        (msg, value, valid_values))
        return mapper.polymorphic_map[value].class_

    @classmethod
    def populate_const_table(cls, table, connection, **kwargs):  # pragma: no cover
        names = inspect(cls).polymorphic_map.keys()
        names.sort()  # beautification only
        stmt = table.insert()
        for name in names:
            try:
                connection.execute(stmt.values(name=name))
            except IntegrityError:
                pass

    @classmethod
    def ddl(self):  # pragma: no cover
        """ Returns the DDL SqlAlchemy will use to generate the table.

            This method is used to aid rapid upgrade sql scripts for new
            tables, but make careful note that it won't properly rename any
            constraints made on a per column basis. The utils.contstraints
            module contains utilities for this and should also be part of the
            creation of any new tables during upgrade procedures """

        return str(CreateTable(self.__table__))

    @classmethod
    def __declare_last__(cls):
        """
        Support __table_args__ with single-table inheritance

        See: http://www.sqlalchemy.org/trac/ticket/2700
        """
        if '__extra_table_args__' in cls.__dict__:
            cls.__table__._init_items(*cls.__extra_table_args__)
            del cls.__extra_table_args__

#Base = declarative_base(metaclass=VersionedMeta, cls=Base)
Base = declarative_base(cls=Base)


# WAY too much magic in AssociationProxy.  This bug and proposed patch is
# listed in the second half of this message:
# http://groups.google.com/group/sqlalchemy-devel/browse_thread/thread/973f4104007f6964/9a001201b3179c58
# Basically, scalar assocation proxies are much more annoying without this
# patch.  Accessing a null attribute normally returns None.  However, the AP
# tries to proxy through the None.  This raises an exception when the AP
# (in a scalar context) should just itself return None.
@monkeypatch(AssociationProxy)
def __get__(self, obj, class_):
    if self.owning_class is None:
        self.owning_class = class_ and class_ or type(obj)
    if obj is None:
        return self
    elif self.scalar is None:
        self.scalar = self._target_is_scalar()
        if self.scalar:
            self._initialize_scalar_accessors()

    if self.scalar:
        # Original line from 0.5.8
        #proxy = self._new(self._lazy_collection(weakref.ref(obj)))
        #setattr(obj, self.key, (id(obj), proxy))
        #return proxy

        target = getattr(obj, self.target_collection)
        if target is None:
            return None
        else:
            return self._scalar_get(target)
    else:
        try:
            # If the owning instance is reborn (orm session resurrect,
            # etc.), refresh the proxy cache.
            creator_id, proxy = getattr(obj, self.key)
            if id(obj) == creator_id:
                return proxy
        except AttributeError:
            pass
        proxy = self._new(_lazy_collection(obj, self.target_collection))
        setattr(obj, self.key, (id(obj), proxy))
        return proxy
