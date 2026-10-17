#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcvjtrb-oalz1s====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcvjtrb-oalz1s exit=${code}====="
exit "$code"
