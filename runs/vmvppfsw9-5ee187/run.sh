#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvppfsw9-5ee187====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvppfsw9-5ee187 exit=${code}====="
exit "$code"
