#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxqzlvs-iey7dk====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'numpy'
  python 'simulator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxqzlvs-iey7dk exit=${code}====="
exit "$code"
