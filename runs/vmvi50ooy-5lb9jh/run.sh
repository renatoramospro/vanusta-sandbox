#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvi50ooy-5lb9jh====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvi50ooy-5lb9jh exit=${code}====="
exit "$code"
