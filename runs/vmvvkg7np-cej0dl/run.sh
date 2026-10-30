#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvvkg7np-cej0dl====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvvkg7np-cej0dl exit=${code}====="
exit "$code"
