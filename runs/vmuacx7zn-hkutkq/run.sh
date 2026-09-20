#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuacx7zn-hkutkq====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuacx7zn-hkutkq exit=${code}====="
exit "$code"
