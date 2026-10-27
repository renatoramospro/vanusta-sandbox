#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvr0lbep-x7va27====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvr0lbep-x7va27 exit=${code}====="
exit "$code"
