#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwuc9u4k-og42i7====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwuc9u4k-og42i7 exit=${code}====="
exit "$code"
