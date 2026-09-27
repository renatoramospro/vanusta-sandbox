#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujtey1m-6og3gz====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujtey1m-6og3gz exit=${code}====="
exit "$code"
