#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh5sff6-ki8sqr====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh5sff6-ki8sqr exit=${code}====="
exit "$code"
