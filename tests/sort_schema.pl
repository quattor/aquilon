#! /ms/dist/perl5/bin/perl5.10 -W
#
# Copyright (C) 2011,2013  Contributor
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

# Crude script to sort the fields and constraints of an Oracle schema dump
#
# This script re-arranges the output of the schema_dump.sql PL/SQL script.
#
# Since Oracle does not allow specifying the position when columns/constraints
# are added or removed, after a while the order of items in the prod schema
# becomes different from a newly generated schema. This script tries to help
# comparing two schemas.
# 
# Known bugs: the first column and the last constraint are not reordered, so
# the output is still not always identical when the DB schemas are otherwise
# equal

use strict;

my $prev;
my @constraints;
my @fields;

while (my $line = <>) {
	chomp $line;
	next unless $line;
	if ($line =~ m/^\s+"/) {
		$line =~ s/,$//;
		push @fields, $line;
	}
	elsif ($line =~ m/^\s+CONSTRAINT/) {
		if (@fields) {
			print join(",\n", sort @fields), ",\n";
			undef @fields;
		}
		$line =~ s/,$//;
		push @constraints, $prev if $prev;
		$prev = $line;
	}
	elsif ($line =~ m/^\s+REFERENCES/ && $prev) {
		$line =~ s/^\s+//;
		$line =~ s/,$//;
		$prev .= " " . $line;
	}
	else {
		if (@fields) {
			print join(",\n", sort @fields), ",\n";
			undef @fields;
		}
		if ($prev) {
			push @constraints, $prev;
			undef $prev;
		}
		if (@constraints) {
			print join(",\n", sort @constraints), "\n";
			undef @constraints;
		}
		print $line, "\n";
	}
}
