#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvv6etew-a65h7i====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvv6etew-a65h7i exit=${code}====="
exit "$code"
