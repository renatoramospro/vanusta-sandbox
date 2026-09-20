#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua4sfqz-010u38====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua4sfqz-010u38 exit=${code}====="
exit "$code"
