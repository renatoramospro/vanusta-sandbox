#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwul266l-ydra54====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwul266l-ydra54 exit=${code}====="
exit "$code"
