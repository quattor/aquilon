# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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
import sys

from inspect import isclass

from sqlalchemy.orm.session import Session
from sqlalchemy.orm.properties import RelationProperty
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.ext.associationproxy import AssociationProxy, _lazy_collection

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
            if not hasattr(type(self), k):
                msg = "%r is an invalid argument for %s" % (
                    k, type(self).__name__)
                raise TypeError(msg)
            setattr(self, k, kw[k])

    def __repr__(self):
        # This functions much more like a __str__ than a __repr__...
        return "%s %s" % (self.__class__._get_class_label(),
                          self._get_instance_label())

    @classmethod
    def _get_class_label(cls):
        return getattr(cls, "_class_label", cls.__name__)

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
        mapper = cls.__mapper__
        caller = sys._getframe(1).f_code.co_name
        clslabel = cls._get_class_label()

        if not isinstance(session, Session):
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
            if mapper.has_property(field):
                rel = mapper.get_property(field)
                if isinstance(rel, RelationProperty) and \
                        not isinstance(value, rel.argument):
                    value = rel.argument.get_unique(session, value,
                                                    compel=compel)

            # filter_by() would be simpler but it would not allow querying just
            # one column
            query = query.filter(getattr(cls, field) == value)

            # Now some beautification...
            poly_column = getattr(mapper, "polymorphic_on", None)
            if poly_column is not None and poly_column.name == field:
                # Return "Building foo" instead of "Location foo, location_type
                # building"
                clslabel = mapper.polymorphic_map[value].class_._get_class_label()
            else:
                name = value.name if hasattr(value, "name") else str(value)
                if field == "name":
                    desc.append(name)
                else:
                    desc.append(field + " " + name)

        # Check for arguments we don't know about
        if kwargs:
            raise InternalError("Extra arguments to %s(): %s." %
                                (caller, kwargs))
        return (query, clslabel, desc)

    @classmethod
    def get_unique(cls, session, *args, **kwargs):
        compel = kwargs.get('compel', False)
        preclude = kwargs.pop('preclude', False)

        query = session.query(cls)
        (query, clslabel, desc) = cls._selection_helper(session, query, *args,
                                                        **kwargs)
        try:
            obj = query.one()
            if preclude:
                msg = "%s %s already exists." % (clslabel, ", ".join(desc))
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
        query = session.query(cls.__table__.c.id)
        (query, clslabel, desc) = cls._selection_helper(session, query, *args,
                                                        **kwargs)
        if compel:
            obj = query.first()
            if obj is None:
                msg = "%s %s not found." % (clslabel, ", ".join(desc))
                _raise_custom(compel, NotFoundException, msg)
        return query.subquery()


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
