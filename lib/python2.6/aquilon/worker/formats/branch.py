# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
        if domain.change_manager:
            details.append(indent + "  Change Manager: %s" %
                           domain.change_manager)
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
