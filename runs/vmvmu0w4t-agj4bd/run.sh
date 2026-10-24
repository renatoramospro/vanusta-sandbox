#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvmu0w4t-agj4bd====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvmu0w4t-agj4bd exit=${code}====="
exit "$code"
