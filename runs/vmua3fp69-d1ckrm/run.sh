#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua3fp69-d1ckrm====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua3fp69-d1ckrm exit=${code}====="
exit "$code"
