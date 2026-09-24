#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufzole0-13w6t8====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufzole0-13w6t8 exit=${code}====="
exit "$code"
