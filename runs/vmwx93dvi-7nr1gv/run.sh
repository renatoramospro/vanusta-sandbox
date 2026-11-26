#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx93dvi-7nr1gv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx93dvi-7nr1gv exit=${code}====="
exit "$code"
