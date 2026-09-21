#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubf30gy-gxitiq====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubf30gy-gxitiq exit=${code}====="
exit "$code"
