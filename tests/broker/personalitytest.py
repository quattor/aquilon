# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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
""" Helper classes for personality testing """

default_parameters = {
    'aquilon': {
        "espinfo/function": "development",
        "espinfo/class": "INFRASTRUCTURE",
        "espinfo/users": "IT / TECHNOLOGY",
        "espinfo/threshold": 0
    },
    'vmhost': {
        "espinfo/function": "development",
        "espinfo/class": "INFRASTRUCTURE",
        "espinfo/users": "IT / TECHNOLOGY",
    },
}

clustered_archetypes = ["vmhost"]


class PersonalityTestMixin(object):
    def setup_personality(self, archetype, name, maps=None, required=None):
        if archetype in default_parameters:
            for path, value in default_parameters[archetype].items():
                self.noouttest(["add_parameter", "--archetype", archetype,
                                "--personality", name,
                                "--path", path, "--value", value])

        if required:
            for service in required:
                self.noouttest(["add_required_service", "--service", service,
                                "--archetype", archetype, "--personality", name])

        if maps:
            for service, mappings in maps.items():
                for instance, locations in mappings.items():
                    for loc_type, loc_names in locations.items():
                        for loc_name in loc_names:
                            self.noouttest(["map_service", "--service", service,
                                            "--instance", instance,
                                            "--" + loc_type, loc_name,
                                            "--personality", name,
                                            "--archetype", archetype])

    def create_personality(self, archetype, name, environment="dev",
                           grn="grn:/ms/ei/aquilon/unittest", comments=None, maps=None,
                           required=None):
        """ Create the given personality with reasonable defaults. """

        command = ["add_personality", "--archetype", archetype,
                   "--personality", name, "--grn", grn,
                   "--host_environment", environment]
        if archetype in clustered_archetypes:
            command.append("--cluster_required")
        if comments:
            command.extend(["--comments", comments])
        self.noouttest(command)

        self.setup_personality(archetype, name, maps=maps, required=required)

    def drop_personality(self, archetype, name):
        # Ok, not much here yet. In the future, this helper may be used to
        # automatically get rid of any dependencies that would prevent the
        # personality from being removed.
        self.noouttest(["del_personality", "--archetype", archetype,
                        "--personality", name])
