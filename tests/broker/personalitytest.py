# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013,2015,2016  Contributor
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
        "windows/windows": '[{"duration": 8, "start": "08:00", "day": "Sun"}]',
    },
    'esx_cluster': {
        "espinfo/class": "INFRASTRUCTURE",
        "windows/windows": '[{"duration": 8, "start": "08:00", "day": "Sun"}]',
    },
    'hacluster': {
        "espinfo/class": "INFRASTRUCTURE",
    },
    'vmhost': {
        "espinfo/function": "development",
        "espinfo/class": "INFRASTRUCTURE",
        "espinfo/users": "IT / TECHNOLOGY",
        "windows/windows": '[{"duration": 8, "start": "08:00", "day": "Sun"}]',
    },
}

clustered_archetypes = ["vmhost"]


class PersonalityTestMixin(object):
    def setup_personality(self, archetype, name, maps=None, required=None):
        if archetype in default_parameters:
            for path, value in default_parameters[archetype].items():
                command = ["add_parameter", "--archetype", archetype,
                           "--personality", name,
                           "--path", path, "--value", value]
                self.noouttest(command)

        if required:
            for service in required:
                command = ["add_required_service", "--service", service,
                           "--archetype", archetype, "--personality", name]
                self.noouttest(command)

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
                           grn="grn:/ms/ei/aquilon/unittest", staged=False,
                           comments=None, maps=None, required=None,
                           cluster_required=None, config_override=None):
        """ Create the given personality with reasonable defaults. """

        command = ["add_personality", "--archetype", archetype,
                   "--personality", name, "--grn", grn,
                   "--host_environment", environment]
        if cluster_required or archetype in clustered_archetypes:
            command.append("--cluster_required")

        if staged is not None:
            if staged:
                command.append("--staged")
            else:
                command.append("--unstaged")
        if config_override:
            command.append("--config_override")
        if staged:
            command.append("--staged")
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

    def verifycatpersonality(self, archetype, personality,
                             config_override=False, host_env='dev', grn=None,
                             stage=None):
        if stage and stage != "current":
            staged_name = "%s+%s" % (personality, stage)
        else:
            staged_name = personality

        command = ["cat", "--archetype", archetype, "--personality", personality]
        if stage:
            command.extend(["--personality_stage", stage])
        out = self.commandtest(command)
        self.matchoutput(out, 'variable PERSONALITY = "%s"' % staged_name,
                         command)
        if grn:
            self.check_personality_grns(out, grn, {"esp": [grn]}, command)

        self.matchoutput(out, "template personality/%s/config;" % staged_name,
                         command)
        self.matchoutput(out, '"/system/personality/name" = "%s";' % personality,
                         command)
        self.matchoutput(out, 'final "/system/personality/host_environment" = "%s";' % host_env,
                         command)

        if config_override:
            self.matchoutput(out, 'include { "features/personality/config_override/config" };',
                             command)
        else:
            self.matchclean(out, 'config_override', command)

        if stage is None:
            self.matchclean(out, "/system/personality/stage", command)
        else:
            self.matchoutput(out, '"/system/personality/stage" = "%s";' % stage,
                             command)
