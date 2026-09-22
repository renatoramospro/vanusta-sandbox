#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucmogob-rshoze====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucmogob-rshoze exit=${code}====="
exit "$code"
