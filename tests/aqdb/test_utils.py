#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

""" Some quick meta-tests for our utility library """

import utils
utils.load_classpath()

import nose
from nose.tools import eq_

def test_func_name():
    eq_(utils.func_name(), 'test_utils.test_func_name()')

    print '\ntests.aqdb.utils.func_name returns %s' % utils.func_name()

#TODO: test the nose plugin with the recipe in it

if __name__ == "__main__":
    nose.runmodule()
