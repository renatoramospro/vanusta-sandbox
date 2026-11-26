#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxwkakg-q3qpt1====="
(
  set -e
  python 'io_non_blocking.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxwkakg-q3qpt1 exit=${code}====="
exit "$code"
