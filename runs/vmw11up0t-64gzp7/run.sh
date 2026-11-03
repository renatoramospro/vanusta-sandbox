#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmw11up0t-64gzp7====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmw11up0t-64gzp7 exit=${code}====="
exit "$code"
