#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvzvextz-fc4ir4====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvzvextz-fc4ir4 exit=${code}====="
exit "$code"
