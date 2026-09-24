#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufuiyju-kb63te====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufuiyju-kb63te exit=${code}====="
exit "$code"
