#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk7ycgj-xjsanf====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk7ycgj-xjsanf exit=${code}====="
exit "$code"
