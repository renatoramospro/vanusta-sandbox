#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxlqsjm-4973k6====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxlqsjm-4973k6 exit=${code}====="
exit "$code"
