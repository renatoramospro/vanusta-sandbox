#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubwupo2-o7am6b====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubwupo2-o7am6b exit=${code}====="
exit "$code"
