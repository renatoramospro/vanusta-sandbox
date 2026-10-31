#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvwqzv6u-q2unj7====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvwqzv6u-q2unj7 exit=${code}====="
exit "$code"
