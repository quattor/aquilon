#! /usr/bin/env perl
#
# Copyright (C) 2014  Contributor
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

use MSDW::Version
	'CDB_File'          => '0.97',
	'FreezeThaw'        => '0.43',
	'XML-SAX'           => '0.15',
	'XML-LibXML'        => '1.90-2.7.8',
	'storage/stormap'   => '1.6',
;

use stormap;

my $stormap = stormap->new();
$stormap->optimize('speed');
$stormap->stormap_load("testnasobjects.map") || die($stormap->get_logs());
$stormap->map();
$stormap->write_cdb("testnasobjects.cdb") || die($stormap->get_logs());
