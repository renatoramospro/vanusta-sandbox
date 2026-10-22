#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvjkkeau-o1qmp3====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvjkkeau-o1qmp3 exit=${code}====="
exit "$code"
