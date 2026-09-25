#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhabszl-fjwg82====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhabszl-fjwg82 exit=${code}====="
exit "$code"
