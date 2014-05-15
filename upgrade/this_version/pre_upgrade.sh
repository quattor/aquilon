
AQ=aq
ARCHETYPE=netinfra
GRN="grn:/ms/ei/network/tools/NetManSystems"
DOMAIN=netinfra

$AQ add archetype --archetype $ARCHETYPE \
	--nocompilable --description 'ET Devices'

$AQ add domain --domain $DOMAIN --track prod

$AQ add os --osname generic --osversion generic \
	--archetype $ARCHETYPE

$AQ add personality \
        --personality   generic		\
        --archetype     $ARCHETYPE	\
        --grn           $GRN		\
        --host_environment prod


