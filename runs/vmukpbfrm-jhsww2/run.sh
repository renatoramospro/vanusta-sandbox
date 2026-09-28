#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukpbfrm-jhsww2====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukpbfrm-jhsww2 exit=${code}====="
exit "$code"
