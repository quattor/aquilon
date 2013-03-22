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
""" Pull dependencies onto sys.path via ms.version """

import ms.version

ms.version.addpkg('sqlalchemy', '0.7.9')
ms.version.addpkg('cx_Oracle', '5.1-11.2.0.1.0')
ms.version.addpkg('ipython', '0.12.1')
ms.version.addpkg('argparse', '1.1')
ms.version.addpkg('ms.modulecmd', '1.0.4')
ms.version.addpkg('ipaddr', '2.1.9')
ms.version.addpkg('dateutil', '1.5')
