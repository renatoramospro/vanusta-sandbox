#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuj8dp80-0i6cmn====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuj8dp80-0i6cmn exit=${code}====="
exit "$code"
