#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmud1e82p-nmpyj3====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmud1e82p-nmpyj3 exit=${code}====="
exit "$code"
