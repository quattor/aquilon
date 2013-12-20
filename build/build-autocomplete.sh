#!/bin/bash
python bootstrap/gen_completion.py --all
make -f Makefile.rh -C doc
gzip doc/man/man1/*1
