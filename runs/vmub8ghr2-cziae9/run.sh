#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub8ghr2-cziae9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub8ghr2-cziae9 exit=${code}====="
exit "$code"
