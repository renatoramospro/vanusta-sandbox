#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvckxw0g-mzl758====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvckxw0g-mzl758 exit=${code}====="
exit "$code"
