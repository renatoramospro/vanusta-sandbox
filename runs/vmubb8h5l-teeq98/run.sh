#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubb8h5l-teeq98====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubb8h5l-teeq98 exit=${code}====="
exit "$code"
