#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuf4wymt-xpizim====="
(
  set -e
  python 'health_check_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuf4wymt-xpizim exit=${code}====="
exit "$code"
