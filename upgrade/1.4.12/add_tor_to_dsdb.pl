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
my @lines = `aq show_tor_switch --all --format=csv`;
foreach my $line (@lines) {
    chomp $line;
    my @fields = split /,/, $line;
    if (scalar(@fields) < 9) {
        warn "Invalid number of fields in line '$line'";
        next;
    }
    my ($fqdn, $rack, $building, $vendor, $model, $serial, $interface,
        $mac, $ip) = @fields;
    unless ($ip) {
        warn "Skipping tor_switch '$fqdn': No IP information";
        next;
    }
    unless ($fqdn =~ /^[a-zA-Z0-9\.]+$/) {
        warn "Skipping bad tor_switch name '$fqdn'";
        next;
    }
    unless ($ip =~ /^[0-9\.]+$/) {
        warn "Skipping bad IP address '$ip'";
        next;
    }
    $interface =~ s|/|_|g;
    unless ($interface =~ /^[a-zA-Z0-9_]+$/) {
        warn "Skipping bad interface name '$interface'";
        next;
    }
    unless ($mac =~ /^[0-9a-z:]+$/) {
        warn "Skipping bad mac address '$mac'";
        next;
    }
    system("echo dsdb add host -host_name '$fqdn' -ip_address '$ip' -status 'aq' -interface_name '$interface' -ethernet_address '$mac'");
}
