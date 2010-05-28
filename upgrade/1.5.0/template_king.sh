#!/bin/sh -ex

QUATTORDIR=/var/quattor

TEMPLATE_KING=$QUATTORDIR/template-king
TEMPLATE_KING_OLD=$TEMPLATE_KING.old

mv $TEMPLATE_KING $TEMPLATE_KING_OLD
git clone --bare $TEMPLATE_KING_OLD $TEMPLATE_KING

cd $TEMPLATE_KING
git branch -m master prod

DOMAINS=$QUATTORDIR/domains
mkdir -p $DOMAINS

OLD_TEMPLATES=$QUATTORDIR/templates

cd $OLD_TEMPLATES
for i in * ; do
	if [ "$i" = "ny-prod" ] ; then
		continue
	fi
	if [ "$i" = "ny-qa" ] ; then
		continue
	fi
	if [ ! -d "$OLD_TEMPLATES/$i/aquilon" ] ; then
		# Skip empty/broken repos
		continue
	fi
	cd $TEMPLATE_KING
	git remote add legacy_$i $OLD_TEMPLATES/$i
	git fetch legacy_$i
	git branch --no-track $i legacy_$i/master
	git remote rm legacy_$i
done

cd $TEMPLATE_KING
git remote add legacy_ny-qa $OLD_TEMPLATES/ny-qa
git fetch legacy_ny-qa
git branch --no-track qa legacy_ny-qa/master
git remote rm legacy_ny-qa

git branch --track ny-prod prod
git branch --track ny-qa qa

cd $DOMAINS
for i in prod qa ny-prod ny-qa ; do
	git clone --branch $i $TEMPLATE_KING $i
done

