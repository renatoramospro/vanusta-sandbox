#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua5p6yr-0mnpzb====="
(
  set -e
  python 'cubo.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua5p6yr-0mnpzb exit=${code}====="
exit "$code"
