#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukbxaqv-2zwb91====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukbxaqv-2zwb91 exit=${code}====="
exit "$code"
