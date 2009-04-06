#!/bin/bash

DB="AQUILON"
read -p "using database $DB. ok? (y/n) " OK

if [ "$OK" != "y" ] ; then
    echo "Goodbye"
    exit
fi

echo 
read -s -p "provide the cdb password> " PASSWD
echo 

sqlplus -S cdb/"$PASSWD"@"$DB" @personality_upgrade
sqlplus -S cdb/"$PASSWD"@"$DB" @archetype_upgrade
sqlplus -S cdb/"$PASSWD"@"$DB" @analyze

