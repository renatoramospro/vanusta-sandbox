#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubv13c9-dx6ztg====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubv13c9-dx6ztg exit=${code}====="
exit "$code"
