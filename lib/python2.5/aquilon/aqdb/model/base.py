# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
import weakref
from inspect import isclass

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy import Integer
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.orm.properties import RelationProperty

from aquilon.utils import monkeypatch
from aquilon.exceptions_ import InternalError, NotFoundException, ArgumentError
#These extensions will be coming soon...
#from aquilon.aqdb.history.history_meta import VersionedMeta
#from aquilon.aqdb.history.audit import audit_listener_for_class


def _describe_uniqueness_request(cls, *args, **kwargs):
    """Helper method for constructing errors in Base.get_unique()."""
    if kwargs:
        extras = []
        for (k, v) in kwargs.items():
            if isinstance(v, Base):
                # Do something more interesting than str()?
                extras.append(str(v))
            else:
                extras.append("%s of '%s'" % (k, v))
        kwstr = " and ".join(extras)
    if kwargs and args:
        criteria = " '%s' with %s" % (args[0], kwstr)
    elif kwargs:
        criteria = " with %s" % kwstr
    elif args:
        criteria = " '%s'" % args[0]
    else:
        criteria = ""
    return "%s%s" % (cls._get_class_label(), criteria)


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
    def get_by(cls, k, v, session):
        return session.query(cls).filter(cls.__dict__[k] == v).all()

    @classmethod
    def _get_class_label(cls):
        return getattr(cls, "_class_label", cls.__name__)


    def _get_instance_label(self):
        """Subclasses can override this method or just set a property to check.

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
    def get_unique(cls, session, *args, **kwargs):
        """Use the UniqueConstraints installed on the class to query.

        If there is a single positional arg passed in there can be only
        one unique constraint on the class with a single column.

        Otherwise, use keyword arguments to specify all the columns
        in the uniqueness constraint.  If using keywords some basic
        relational magic is attempted and sqlalchemy objects can be
        passed in.  This is preferred over passing in an id as the
        error message will be more readable.

        If compel is True a NotFoundException will be raised when no
        result is found.  If compel is a valid exception class that type
        of exception will be raised instead.

        If preclude is True an ArgumentException will be raised when
        a result is found.  If preclude is a valid exception class that
        type of exception will be raised instead.

        """
        # Since this method expects positional args to be slurped up
        # into args, these can't be in the method definition.  (If
        # they were, any positional args would be slurped into whichever
        # of these happened to have been defined first!)
        compel = kwargs.pop('compel', False)
        preclude = kwargs.pop('preclude', False)

        if len(args) > 1:
            raise InternalError("Must use keyword arguments for get_unique "
                                "with more than one key.")
        unique_constraints = []
        for constraint in cls.__table__.constraints:
            if isinstance(constraint, UniqueConstraint):
                unique_constraints.append(constraint)
                continue
            if isinstance(constraint, PrimaryKeyConstraint):
                # This is lame.  We want to skip the regular PKCs
                # that just cover an autoincrementing id column.
                # There does not appear to be a good way to
                # differentiate those, though... this is the best
                # we have so far.
                if len(constraint.columns) == 1 and \
                   isinstance(list(constraint.columns)[0].type, Integer) and \
                   list(constraint.keys())[0] not in kwargs:
                    continue
                unique_constraints.append(constraint)
        if len(args) == 1 and len(unique_constraints) > 1:
            raise InternalError("Must use kwargs for get_unique since %s has "
                                "more than one uniqueness constraint." % cls)
        for constraint in unique_constraints:
            query_args = {}
            missing = 0
            for constraint_key in constraint.keys():
                if constraint_key in kwargs:
                    query_args[constraint_key] = kwargs[constraint_key]
                    continue
                # Allow kwargs to be sqlalchemy objects...
                # The trick here is that we need to figure out if any of
                # them could fill in the constraint_key that is being
                # examined.
                found_object = False
                for kwarg in kwargs:
                    if isinstance(kwargs[kwarg], Base) and \
                       cls.__mapper__.has_property(kwarg):
                        rel = cls.__mapper__.get_property(kwarg)
                        if isinstance(rel, RelationProperty) and \
                           len(rel.remote_side) == 1 and \
                           len(rel.local_side) == 1:
                            local_col = list(rel.local_side)[0].name
                            remote_col = list(rel.remote_side)[0].name
                            if constraint_key == local_col:
                                query_args[local_col] = getattr(kwargs[kwarg],
                                                                remote_col)
                                found_object = True
                                break
                if found_object:
                    continue
                # If we don't have the constraint as a keyword argument,
                # try to use the positional args.
                if args:
                    missing += 1
                    query_args[constraint_key] = args[0]
                    continue
                # This constraint isn't going to work.  Next!
                query_args = None
                break
            if missing > 1:
                raise InternalError("Must use kwargs for get_unique since "
                                    "uniqueness constraint for %s requires "
                                    "%s." % (cls, constraint.keys()))
            if query_args:
                result = session.query(cls).filter_by(**query_args).all()
                if not result:
                    if compel:
                        msg = "%s not found." % _describe_uniqueness_request(
                            cls, *args, **kwargs)
                        if isclass(compel) and issubclass(compel, Exception):
                            raise compel(msg)
                        raise NotFoundException(msg)
                    return None
                if len(result) > 1:
                    raise InternalError("Uniqueness constraint violated for "
                                        "%s when querying with %s" %
                                        (cls, query_args))
                if preclude:
                    msg = "%s already exists." % _describe_uniqueness_request(
                        cls, *args, **kwargs)
                    if isclass(preclude) and issubclass(preclude, Exception):
                        raise preclude(msg)
                    raise ArgumentError(msg)
                return result[0]
        if cls.__base__ != cls and hasattr(cls.__base__, '__table__'):
            # This doesn't *really* handle polymorphic inheritance,
            # but it seems to cover our use cases.
            if 'polymorphic_on' in cls.__base__.__mapper_args__ and \
               'polymorphic_identity' in cls.__mapper_args__:
                kwargs[cls.__base__.__mapper_args__['polymorphic_on'].name] = \
                        cls.__mapper_args__['polymorphic_identity']
            return cls.__base__.get_unique(session, *args, **kwargs)
        raise InternalError("No uniqueness constraint found for %s " %
                            _describe_uniqueness_request(cls, *args, **kwargs))


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
        # Original line from 0.5.4
        #return self._scalar_get(getattr(obj, self.target_collection))
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
        proxy = self._new(self._lazy_collection(weakref.ref(obj)))
        setattr(obj, self.key, (id(obj), proxy))
        return proxy
