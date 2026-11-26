#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx9ukqt-67cmiv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx9ukqt-67cmiv exit=${code}====="
exit "$code"
