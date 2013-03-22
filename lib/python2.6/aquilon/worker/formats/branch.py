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
"""Branch formatter."""


import os

from aquilon.config import Config
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import Domain, Sandbox


class DomainFormatter(ObjectFormatter):
    def format_raw(self, domain, indent=""):
        flags = " [autosync]" if domain.autosync else ""
        details = [indent + "Domain: %s%s" % (domain.name, flags)]
        if domain.tracked_branch:
            details.append(indent +
                           "  Tracking: {0:l}".format(domain.tracked_branch))
            details.append(indent + "  Rollback commit: %s" %
                           domain.rollback_commit)
        details.append(indent + "  Validated: %s" % domain.is_sync_valid)
        details.append(indent + "  Owner: %s" % domain.owner.name)
        details.append(indent + "  Compiler: %s" % domain.compiler)
        details.append(indent + "  Requires Change Manager: %s" %
                       domain.requires_change_manager)
        details.append(indent + "  May Contain Hosts/Clusters: %s" %
                       domain.allow_manage)
        if domain.comments:
            details.append(indent + "  Comments: %s" % domain.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Domain] = DomainFormatter()


class AuthoredSandbox(object):
    def __init__(self, dbsandbox, dbauthor):
        self.dbsandbox = dbsandbox
        self.dbauthor = dbauthor
        config = Config()
        templatesdir = config.get('broker', 'templatesdir')
        self.path = os.path.join(templatesdir, dbauthor.name, dbsandbox.name)

    def __getattr__(self, attr):
        return getattr(self.dbsandbox, attr)


class SandboxFormatter(ObjectFormatter):
    def format_raw(self, sandbox, indent=""):
        flags = " [autosync]" if sandbox.autosync else ""
        details = [indent + "Sandbox: %s%s" % (sandbox.name, flags)]
        details.append(indent + "  Validated: %s" % sandbox.is_sync_valid)
        details.append(indent + "  Owner: %s" % sandbox.owner.name)
        details.append(indent + "  Compiler: %s" % sandbox.compiler)
        details.append(indent + "  Base Commit: %s" % sandbox.base_commit)
        if hasattr(sandbox, 'path'):
            details.append(indent + "  Path: %s" % sandbox.path)
        if sandbox.comments:
            details.append(indent + "  Comments: %s" % sandbox.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Sandbox] = SandboxFormatter()
ObjectFormatter.handlers[AuthoredSandbox] = SandboxFormatter()


class RemoteSandbox(object):
    def __init__(self, template_king_url, sandbox_name, user_base):
        self.template_king_url = template_king_url
        self.sandbox_name = sandbox_name
        self.user_base = user_base


class RemoteSandboxFormatter(ObjectFormatter):
    def csv_fields(self, remote_sandbox):
        return (remote_sandbox.template_king_url, remote_sandbox.sandbox_name,
                remote_sandbox.user_base)

ObjectFormatter.handlers[RemoteSandbox] = RemoteSandboxFormatter()
