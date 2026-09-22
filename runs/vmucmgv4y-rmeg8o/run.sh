#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucmgv4y-rmeg8o====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucmgv4y-rmeg8o exit=${code}====="
exit "$code"
