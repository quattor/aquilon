#!/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
"""Unit tests for the aquilon.config module.

We start with the configuration_directory function."""
import os
import sys
import nose
from nose.tools import assert_equals
from aquilon.config import config_filename


def test_configuration_directory():
    assert_equals(config_filename("lkhljhlkjh"),
                  "/usr/share/aquilon/etc/lkhljhlkjh")


if __name__ == '__main__':
    nose.runmodule()
