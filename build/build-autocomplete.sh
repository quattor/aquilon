#!/bin/bash
python bootstrap/gen_completion.py --all
cp VERSION doc/version.txt
make -f Makefile.rh -C doc
gzip doc/man/man1/*1
