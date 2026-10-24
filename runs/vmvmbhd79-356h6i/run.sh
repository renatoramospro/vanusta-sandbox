#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvmbhd79-356h6i====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvmbhd79-356h6i exit=${code}====="
exit "$code"
