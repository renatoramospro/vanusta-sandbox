#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubwfa9k-a991n9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubwfa9k-a991n9 exit=${code}====="
exit "$code"
