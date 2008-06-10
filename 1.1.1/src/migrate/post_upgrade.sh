#!/bin/sh

# Meant to be run after upgrading the server schema to 1.1.1.

VERSION=1.1.1
AQ=/ms/dist/aquilon/PROJ/aqd/$VERSION/bin/aq
AQHOST=oziyp2
AQPORT=6900

for i in cdb njw wesleyhe guyroleh daqscott kgreen benjones; do
	$AQ --aqhost=$AQHOST --aqport=$AQPORT permission --principal=$i@is1.morgan --role=aqd_admin --createuser
done

for i in cesarg jasona dankb goliaa samsh hagberg hookn jelinker kovasck lookerm bet walkert af lillied; do
	$AQ --aqhost=$AQHOST --aqport=$AQPORT permission --principal=$i@is1.morgan --role=engineering --createuser
done

for i in nathand premdasr bestc chawlav wbarnes gleasob lchun peteryip richmoj tipping hardyb martinva coroneld; do
	$AQ --aqhost=$AQHOST --aqport=$AQPORT permission --principal=$i@is1.morgan --role=operations --createuser
done

$AQ --aqhost=$AQHOST --aqport=$AQPORT add service --service afs --instance q.ln.ms.com
$AQ --aqhost=$AQHOST --aqport=$AQPORT add service --service afs --instance q.ny.ms.com
$AQ --aqhost=$AQHOST --aqport=$AQPORT add service --service bootserver --instance np.test
$AQ --aqhost=$AQHOST --aqport=$AQPORT add service --service dns --instance nyinfratest
$AQ --aqhost=$AQHOST --aqport=$AQPORT add service --service ntp --instance pa.ny.na
$AQ --aqhost=$AQHOST --aqport=$AQPORT add service --service lemon
$AQ --aqhost=$AQHOST --aqport=$AQPORT add service --service lemon --instance eng.ln
$AQ --aqhost=$AQHOST --aqport=$AQPORT add service --service syslogng --instance nyb6.np.1

