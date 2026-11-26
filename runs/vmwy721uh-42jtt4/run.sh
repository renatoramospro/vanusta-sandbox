#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwy721uh-42jtt4====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwy721uh-42jtt4 exit=${code}====="
exit "$code"
