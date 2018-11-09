#!/bin/bash
#
# Copyright (C) 2018  Contributor
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

DIR="$(readlink -f "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)")"
GITDIR="$(readlink -f "$(git -C "${DIR}" rev-parse --show-toplevel)")"
HOOKSDIR=${GITDIR}/.git/hooks

HOOKS=("pre-commit")

errors=0
for hook in "${HOOKS[@]}"; do
	hookfrom="${DIR}/${hook}"

	if [ ! -f "${hookfrom}" ]; then
		echo "Error: hook '$hook' does not exist"
		errors=$((errors+1))
		continue
	fi

	hookto="${HOOKSDIR}/${hook}"
	linkto=$(perl -e 'use File::Spec; print File::Spec->abs2rel(@ARGV) . "\n"' \
		 "${hookfrom}" "${HOOKSDIR}")

	if [ -f "${hookto}" ] || [ -L "${hookto}" ]; then
		if [ -L "${hookto}" ] && [ "$(readlink -f "${hookto}")" == "${hookfrom}" ]; then
			echo "Hook '$hook' is already installed as a symbolic link"
			continue
		else
			echo "Error: hook '$hook' already exists; check in .git/hooks/ if it is the right one. The hook was not installed."
			errors=$((errors+1))
			continue
		fi
	fi

	ln -s "${linkto}" "${hookto}"
	echo "Hook '$hook' installed as a symbolic link"
done

exit ${errors}
