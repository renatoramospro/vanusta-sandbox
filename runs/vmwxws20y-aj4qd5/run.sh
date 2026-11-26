#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxws20y-aj4qd5====="
(
  set -e
  python 'io_non_blocking.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxws20y-aj4qd5 exit=${code}====="
exit "$code"
