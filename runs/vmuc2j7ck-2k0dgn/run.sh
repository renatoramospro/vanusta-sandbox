#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuc2j7ck-2k0dgn====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuc2j7ck-2k0dgn exit=${code}====="
exit "$code"
