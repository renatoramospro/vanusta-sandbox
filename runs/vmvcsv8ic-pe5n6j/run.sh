#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcsv8ic-pe5n6j====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcsv8ic-pe5n6j exit=${code}====="
exit "$code"
