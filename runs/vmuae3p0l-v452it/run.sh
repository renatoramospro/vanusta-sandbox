#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuae3p0l-v452it====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuae3p0l-v452it exit=${code}====="
exit "$code"
