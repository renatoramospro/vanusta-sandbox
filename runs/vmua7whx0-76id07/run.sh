#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua7whx0-76id07====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua7whx0-76id07 exit=${code}====="
exit "$code"
