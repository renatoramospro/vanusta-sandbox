#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvfo2in9-x79hnr====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvfo2in9-x79hnr exit=${code}====="
exit "$code"
