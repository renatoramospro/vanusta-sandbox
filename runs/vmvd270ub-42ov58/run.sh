#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvd270ub-42ov58====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvd270ub-42ov58 exit=${code}====="
exit "$code"
