#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuj9d4aw-yrfht9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuj9d4aw-yrfht9 exit=${code}====="
exit "$code"
