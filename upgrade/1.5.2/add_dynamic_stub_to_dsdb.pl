#!/usr/bin/env perl5.8
#
# Copyright (C) 2010,2013  Contributor
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

use strict;
use warnings;

# Assume aq and dsdb are in the path with a correct environment.
my @lines = `aq search system --type=dynamic_stub`;
foreach my $stub (@lines) {
    chomp $stub;
    unless ($stub =~ /dynamic-(\d+)-(\d+)-(\d+)-(\d+)\..*/) {
        warn "Invalid stub '$stub'";
        next;
    }
    my $ip = "$1.$2.$3.$4";
    #system("echo dsdb show host -host_name '$stub' >/dev/null 2>/dev/null");
    #if ($? == 0) {
    #    warn "Stub '$stub' already exists in DSDB.";
    #    next;
    #}
    system("echo dsdb add host -host_name '$stub' -ip_address '$ip' -status 'aq'");
    if ($? != 0) {
        warn "Failed adding '$stub' [$ip] to DSDB: $!";
        next;
    }
}
