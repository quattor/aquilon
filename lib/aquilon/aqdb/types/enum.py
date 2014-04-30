# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013,2014  Contributor
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

import re
from aquilon.exceptions_ import ArgumentError


_StringEnum_Classes = {}


class StringEnum(object):
    def __new__(cls, value):
        if not isinstance(value, str):
            raise TypeError("String expected")
        if cls == StringEnum:
            if not value in _StringEnum_Classes:
                raise ValueError("Unknown StringEnum %s" % value)
            return _StringEnum_Classes[value]
        if not value in cls._StringEnum__lookup:
            raise ValueError("Unknown %s %s" % (cls._class_label(), value))
        ivalue = cls._StringEnum__lookup[value]
        if ivalue._StringEnum__dynamic:
            raise ValueError("Undefined %s %s" % (cls._class_label(), value))
        return ivalue

    def __str__(self):
        return self._StringEnum__value

    def __repr__(self):
        return "%s.%s" % (type(self).__name__, self._StringEnum__name)

    @classmethod
    def _class_label(cls):
        return re.sub(r'([a-z])([A-Z])', r'\1 \2', cls.__name__).lower()

    @classmethod
    def from_argument(cls, label, value):
        if value is None:
            return None
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except TypeError, e:
            raise ArgumentError("Expected a string for %s: %s." % (label, e))
        except ValueError, e:
            raise ArgumentError("Value is not permitted for %s: %s." % (label, e))

    @classmethod
    def from_database(cls, value, permissive=False):
        if not isinstance(value, str):
            raise TypeError("String expected, not %s" % value.__class__)
        if value in cls._StringEnum__lookup:
            return cls._StringEnum__lookup[value]
        if not permissive:
            raise ValueError("Unknown %s %s" % (cls._class_label(), value))
        ivalue = object.__new__(cls)
        ivalue._StringEnum__name = '__UNDEFINED_%s' % value
        ivalue._StringEnum__value = value
        ivalue._StringEnum__dynamic = True
        cls._StringEnum__lookup[value] = ivalue
        return ivalue

    @classmethod
    def to_database(cls, value):
        if isinstance(value, cls):
            return value._StringEnum__value
        if isinstance(value, str):
            if not value in cls._StringEnum__lookup:
                raise ValueError("Unknown %s %s" % (cls._class_label(), value))
            ivalue = cls._StringEnum__lookup[value]
            if ivalue._StringEnum__dynamic:
                raise ValueError("Undefined %s %s" % (cls._class_label(),
                                                      value))
            return value
        raise TypeError("%s or String expected" % cls.__name__)

    class __metaclass__(type):
        def __new__(mcs, clsname, bases, attrs):
            # We get called when StringEnum is created, in this case there
            # is nothing else for us to do, so we just create the class
            if clsname == 'StringEnum':
                return type.__new__(mcs, clsname, bases, attrs)

            # Prevent any additional information from being stored
            attrs['__slots__'] = ['_StringEnum__name', '_StringEnum__value',
                                  '_StringEnum__dynamic']

            # Construct the new class, we return this at the end
            cls = type.__new__(mcs, clsname, bases, attrs)

            # Record the fact we just created this subtype
            _StringEnum_Classes[clsname] = cls

            # Traverse through the inheritance tree.  We are looking to find
            # the higest instance of a StringEnum.  The lookup of that class
            # is then used to populate the static classes.
            parents = []
            super = cls
            while True:
                found = False
                for base in reversed(super.__bases__):
                    if hasattr(base, '_StringEnum__lookup'):
                        parents.append(base)
                        super = base
                        found = True
                        break
                if not found:
                    break

            # Build a lookup table that maps the 'value' of the enum to
            # the statis instance we are about to create
            lookup = {}
            cls._StringEnum__lookup = lookup

            # Returs an 'isa' function for a given name, note this is
            # retquired to avoid scope issues of key
            def _make_isa_inst(obj):
                return lambda self: self is obj

            # Process all of the attributes of the class that is being
            # constructed, building the class as we go
            for name, value in attrs.iteritems():
                # Skip any reserved names
                if name.startswith('_'):
                    continue

                # String attibutes create a static instance of this class
                if isinstance(value, str):
                    # Create a new object storing the name and value
                    ivalue = object.__new__(cls)
                    ivalue._StringEnum__name = name
                    ivalue._StringEnum__value = value
                    ivalue._StringEnum__dynamic = False
                    # Retain a mapping between the value and the instance
                    lookup[value] = ivalue
                    # Update the attribute to be the static class
                    setattr(cls, name, ivalue)
                    # Provide an 'isa' function for this name
                    setattr(super, 'is%s' % name, _make_isa_inst(ivalue))

            def _make_isa_set(lookup):
                return lambda self: self._StringEnum__value in lookup
            setattr(super, 'is%s' % clsname, _make_isa_set(lookup))

            # Run throuh our inheritance tree adding our types to our
            # parents are we go.  This ensures the super types always
            # can instanciate us as a subtype
            for parent in parents:
                plookup = getattr(parent, '_StringEnum__lookup')
                plookup.update(lookup)

            # Return the newly created type
            return cls
