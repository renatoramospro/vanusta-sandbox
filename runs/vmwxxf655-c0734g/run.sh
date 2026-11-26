#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxxf655-c0734g====="
(
  set -e
  python 'io_non_blocking.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxxf655-c0734g exit=${code}====="
exit "$code"
