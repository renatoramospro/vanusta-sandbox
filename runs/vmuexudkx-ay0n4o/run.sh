#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuexudkx-ay0n4o====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuexudkx-ay0n4o exit=${code}====="
exit "$code"
