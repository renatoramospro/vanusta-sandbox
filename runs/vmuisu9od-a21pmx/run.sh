#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuisu9od-a21pmx====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuisu9od-a21pmx exit=${code}====="
exit "$code"
