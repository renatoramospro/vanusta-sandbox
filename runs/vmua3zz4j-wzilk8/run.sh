#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua3zz4j-wzilk8====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua3zz4j-wzilk8 exit=${code}====="
exit "$code"
