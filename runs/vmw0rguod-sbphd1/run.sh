#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmw0rguod-sbphd1====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmw0rguod-sbphd1 exit=${code}====="
exit "$code"
