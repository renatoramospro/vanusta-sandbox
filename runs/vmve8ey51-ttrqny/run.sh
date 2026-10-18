#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmve8ey51-ttrqny====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmve8ey51-ttrqny exit=${code}====="
exit "$code"
