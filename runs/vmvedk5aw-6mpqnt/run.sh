#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvedk5aw-6mpqnt====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvedk5aw-6mpqnt exit=${code}====="
exit "$code"
