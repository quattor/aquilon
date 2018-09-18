# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""
Define parametrized objects, this is a special class that aims at containing
a number of different database objects, with a main one, which is the one
getting "parametrized".  This is basically a wrapper around that object and
other parameters to specify the application of that object.

The reason this file is put in aqdb/model instead of worker/dbwrappers is that
it is used by some database objects to return parametrized objects.
"""


class Parameterized(object):
    _objects = {}

    @classmethod
    def get(cls, *args, **kwargs):
        obj = None
        for subclass in cls.__subclasses__():
            try:
                obj = subclass(*args, **kwargs)
            except TypeError:
                pass
            else:
                break

        if not obj:
            raise TypeError('no subclass found to match parameters '
                            '({}, {})'.format(args, kwargs))

        return obj

    def __init__(self, *args, **kwargs):
        objects = {}

        for k, v in kwargs.items():
            # Check that the key exists in the _objects definition, as if it
            # does not, we want to raise an exception
            if k not in self._objects:
                raise TypeError('__init__() got an unexpected keyword '
                                'argument \'{}\''.format(k))

            # Store the attribute
            objects[k] = v

        for v in args:
            # Get all the parameters of the same type as the object
            params = [name for name, cls in self._objects.items()
                      if issubclass(v.__class__, cls)]
            if not params:
                raise TypeError('__init__() got an unexpected argument '
                                'of type \'{}\''.format(v.__class__.__name__))

            # If we found any, check that they have not been already set
            # with kwargs, and select the first one to store our attribute
            k = None
            for param in params:
                if param not in objects:
                    k = param
                    break

            if not k:
                raise TypeError('__init__() got an unexpected extra argument '
                                'of type \'{}\''.format(v.__class__.__name__))

            # Store the attribute, we do not need to check if the key exists
            # in the _objects definition, as we found the key from there
            # already
            objects[k] = v

        # If there is any parameter missing, raise an exception
        missing = set(self._objects.keys()) - set(objects.keys())
        if missing:
            raise TypeError(
                'Missing parameters to initialize object of type {}: '
                '{}'.format(
                    self.__class__.__name__,
                    ''.join('\'{}\' ({})'.format(k, self._objects[k].__name__)
                            for k in missing)))

        objects['_main'] = objects['main']
        for k, v in objects.items():
            setattr(self, k, v)

    @property
    def main_object(self):
        return self._main

    @property
    def all_objects(self):
        return [self._main] + [
            getattr(self, attr)
            for attr in sorted(self._objects.keys())
            if attr != 'main']

    def __getattribute__(self, name):
        if name == 'get' and self.get == Parameterized.get and \
                getattr(self, '_main', None):
            raise AttributeError('Attribute \'get\' does not exist')
        return super(Parameterized, self).__getattribute__(name)

    def __getattr__(self, attr):
        return getattr(self._main, attr)

    def __format__(self, fmt):
        return ', '.join(format(obj, fmt) for obj in self.all_objects)

    def __eq__(self, other):
        if not isinstance(other, self.__class__) or (
                set(other._objects.items()) ^ set(self._objects.items())):
            return False
        return all(getattr(other, name) == getattr(self, name)
                   for name in self._objects.keys())

    def __hash__(self):
        return hash(getattr(self, name) for name in self._objects.keys())
