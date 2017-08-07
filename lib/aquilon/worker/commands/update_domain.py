# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2016,2017  Contributor
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
"""Contains the logic for `aq update domain`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Domain
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.branch import (expand_compiler,
                                              has_compileable_objects)
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUpdateDomain(BrokerCommand):

    required_parameters = ["domain"]

    def render(self, session, domain, comments, compiler_version, auto_compile,
               autosync, change_manager, allow_manage, profile_formats,
               archived, user, justification, reason, logger, **_):
        dbdomain = Domain.get_unique(session, domain, compel=True)

        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        cm.consider(dbdomain)
        cm.validate()

        if comments is not None:
            dbdomain.comments = comments

        if compiler_version:
            dbdomain.compiler = expand_compiler(self.config, compiler_version)

        if autosync is not None:
            dbdomain.autosync = autosync

        if auto_compile is not None:
            dbdomain.auto_compile = auto_compile

        if change_manager is not None:
            if dbdomain.tracked_branch:
                raise ArgumentError("Cannot enforce a change manager for "
                                    "tracking domains.")
            dbdomain.requires_change_manager = change_manager

        if archived is not None:
            if archived:
                if dbdomain.tracked_branch:
                    raise ArgumentError("{0} is a tracking domain and cannot "
                                        "be archived.".format(dbdomain))
                dbdomain.allow_manage = False
            dbdomain.archived = archived

        if allow_manage is not None:
            if allow_manage and dbdomain.archived:
                raise ArgumentError("{0} is archived, cannot allow managing "
                                    "hosts to it.".format(dbdomain))
            dbdomain.allow_manage = allow_manage

        if profile_formats is not None:
            # We don't want to deal with cleaning up existing profiles if the
            # formats change, so we don't allow changing the format if there are
            # compileable objects
            if has_compileable_objects(dbdomain):
                raise ArgumentError("{0} has compileable objects, the profile "
                                    "format cannot be changed."
                                    .format(dbdomain))
            dbdomain.formats = profile_formats

        session.flush()
        return
