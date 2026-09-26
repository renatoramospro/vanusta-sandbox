#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhr0fdz-qv36ip====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhr0fdz-qv36ip exit=${code}====="
exit "$code"
