#! /bin/sh
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
