#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujay8dk-mcobqk====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujay8dk-mcobqk exit=${code}====="
exit "$code"
