#!/usr/bin/env perl5.8

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
