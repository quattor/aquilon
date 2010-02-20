#!/usr/bin/env perl5.8

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
    #if ($interface eq "gigabitethernet0/1") {
    #    $interface = "xge49";
    #}
    unless ($interface =~ /^[a-zA-Z0-9]+$/) {
        warn "Skipping bad interface name '$interface'";
        next;
    }
    unless ($mac =~ /^[0-9a-z:]+$/) {
        warn "Skipping bad mac address '$mac'";
        next;
    }
    system("echo dsdb add host -host_name '$fqdn' -ip_address '$ip' -status 'aq' -interface_name '$interface' -ethernet_address '$mac'");
}
