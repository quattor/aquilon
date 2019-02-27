# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2014,2018-2019  Contributor
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
"""User formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import (
    User,
    UserType,
)


class UserTypeFormatter(ObjectFormatter):
    def format_raw(self, user_type, indent="", embedded=True,
                   indirect_attrs=True):
        details = []

        details.append('{}User type: {}'.format(
            indent, user_type.name))

        if user_type.comments:
            details.append('{}  Comments: {}'.format(
                indent, user_type.comments))

        return '\n'.join(details)


ObjectFormatter.handlers[UserType] = UserTypeFormatter()


class UserFormatter(ObjectFormatter):
    def format_raw(self, user, indent="", embedded=True, indirect_attrs=True):
        details = [indent + "User: %s" % user.name]
        details.append(indent + "  Type: %s" % user.type.name)
        details.append(indent + "  UID: %s" % user.uid)
        details.append(indent + "  GID: %s" % user.gid)
        details.append(indent + "  Full Name: %s" % user.full_name)
        details.append(indent + "  Home Directory: %s" % user.home_dir)
        return "\n".join(details)

    def fill_proto(self, user, skeleton, embedded=True, indirect_attrs=True):
        skeleton.name = user.name
        skeleton.type = user.type.name
        skeleton.uid = user.uid
        skeleton.gid = user.gid
        skeleton.fullname = user.full_name
        skeleton.homedir = user.home_dir

    def csv_fields(self, user):
        yield (user.name, user.uid, user.gid, user.name, user.home_dir)


ObjectFormatter.handlers[User] = UserFormatter()
