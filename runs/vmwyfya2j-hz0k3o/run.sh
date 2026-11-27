#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyfya2j-hz0k3o====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyfya2j-hz0k3o exit=${code}====="
exit "$code"
