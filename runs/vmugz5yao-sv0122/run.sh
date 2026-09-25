#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugz5yao-sv0122====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugz5yao-sv0122 exit=${code}====="
exit "$code"
