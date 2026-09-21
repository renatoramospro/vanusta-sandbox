#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubds0jh-jjk3g7====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubds0jh-jjk3g7 exit=${code}====="
exit "$code"
