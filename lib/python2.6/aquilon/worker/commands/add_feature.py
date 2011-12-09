# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011  Contributor
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

import re

from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import Feature
from aquilon.exceptions_ import ArgumentError, UnimplementedError

# Do not allow path components to start with '.' to avoid games like "../foo" or
# hidden directories like ".foo/bar"
_name_re = re.compile(r'^\.|[/\\]\.')

class CommandAddFeature(BrokerCommand):

    required_parameters = ['feature', 'type']

    def render(self, session, feature, type, post_personality, comments,
               **arguments):
        Feature.validate_type(type)

        if _name_re.search(feature):
            raise ArgumentError("Path components in the feature name must not "
                                "start with a dot.")

        cls = Feature.__mapper__.polymorphic_map[type].class_

        if post_personality and not cls.post_personality_allowed:
            raise UnimplementedError("The post_personality attribute is "
                                     "implemented only for host features.")

        cls.get_unique(session, name=feature, preclude=True)

        dbfeature = cls(name=feature, post_personality=post_personality,
                        comments=comments)
        session.add(dbfeature)

        session.flush()

        return
