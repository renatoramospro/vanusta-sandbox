#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukozyiu-2wlpb9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukozyiu-2wlpb9 exit=${code}====="
exit "$code"
