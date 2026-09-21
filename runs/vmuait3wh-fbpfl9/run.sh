#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuait3wh-fbpfl9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuait3wh-fbpfl9 exit=${code}====="
exit "$code"
