# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011  Contributor
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
"""Contains the logic for `aq search esx cluster`."""


from aquilon.worker.broker import BrokerCommand
from aquilon.worker.commands.search_cluster import CommandSearchCluster


class CommandSearchESXCluster(CommandSearchCluster):

    required_parameters = []

    def render(self, **arguments):
        gen_arguments = {}

        esx_hostname = None

        # translate option names for search cluster command.
        for key in arguments:
            # change locations prefix
            if key.startswith('vmhost_'):
                gen_arguments[key.replace('vmhost_', 'member_')] = \
                    arguments[key]
            # esx_hostname > member_hostname
            elif key == 'esx_hostname':
                esx_hostname = arguments[key]
            # 'esx_' prefix to these options.
            elif key in [
                'metacluster', 'guest', 'share', 'switch', 'virtual_machine']:
                gen_arguments["esx_%s" % key] = arguments[key]
            else:
                gen_arguments[key] = arguments[key]

        return CommandSearchCluster.render(self, cluster_type='esx',
            allowed_archetype=None, allowed_personality=None,
            down_hosts_threshold=None,
            down_maint_threshold=None,  # fullinfo=None,
            location=None, max_members=None, member_archetype=None,
            member_hostname=esx_hostname, member_personality=None,
            **gen_arguments)
