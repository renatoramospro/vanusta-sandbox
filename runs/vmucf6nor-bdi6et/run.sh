#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucf6nor-bdi6et====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucf6nor-bdi6et exit=${code}====="
exit "$code"
