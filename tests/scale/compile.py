#!/usr/bin/env python
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
"""Compile a domain."""


from common import AQRunner


def compile(domain, aqservice, aqhost, aqport):
    aq = AQRunner(aqservice=aqservice, aqhost=aqhost, aqport=aqport)
    print "Compiling domain %s" % domain
    rc = aq.wait(["compile", "--domain=%s" % domain])


if __name__=='__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-d", "--domain", dest="domain", type="string",
                      help="The domain to compile")
    parser.add_option("-a", "--aqservice", dest="aqservice", type="string",
                      help="The service name to use when connecting to aqd")
    parser.add_option("-t", "--aqhost", dest="aqhost", type="string",
                      help="The aqd host to connect to")
    parser.add_option("-p", "--aqport", dest="aqport", type="string",
                      help="The port to use when connecting to aqd")
    (options, args) = parser.parse_args()
    if not options.domain:
        parser.error("Missing option --domain")

    compile(options.domain, options.aqservice, options.aqhost, options.aqport)
