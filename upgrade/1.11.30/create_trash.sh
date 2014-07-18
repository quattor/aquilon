#! /bin/sh
#
# Create a disconnected branch named 'trash'

set -e

DIR=`mktemp -d`
cd $DIR
git clone --no-checkout /var/quattor/template-king
cd template-king
git checkout --orphan trash
git rm -rf .
git clean -dfx
touch .empty
git add .empty
git commit -m 'Empty initial commit'
git push origin trash

cd /
rm -rf "$DIR"
