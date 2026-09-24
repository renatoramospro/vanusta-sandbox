#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufvf0ds-vwaz4s====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufvf0ds-vwaz4s exit=${code}====="
exit "$code"
