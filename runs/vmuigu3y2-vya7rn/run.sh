#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuigu3y2-vya7rn====="
(
  set -e
  python 'di_container.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuigu3y2-vya7rn exit=${code}====="
exit "$code"
