#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuexezew-zfdkkb====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuexezew-zfdkkb exit=${code}====="
exit "$code"
