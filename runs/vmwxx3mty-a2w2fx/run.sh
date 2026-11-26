#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxx3mty-a2w2fx====="
(
  set -e
  python 'io_non_blocking.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxx3mty-a2w2fx exit=${code}====="
exit "$code"
