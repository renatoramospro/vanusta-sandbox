#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcnq7bk-gsvmgr====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcnq7bk-gsvmgr exit=${code}====="
exit "$code"
