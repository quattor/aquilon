#! /usr/bin/env perl
#
# Small helper for converting a stormap text dump file to CDB format

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
