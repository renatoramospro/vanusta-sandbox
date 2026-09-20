#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua5hrbz-nxui9h====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua5hrbz-nxui9h exit=${code}====="
exit "$code"
