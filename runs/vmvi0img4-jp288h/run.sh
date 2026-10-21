#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvi0img4-jp288h====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvi0img4-jp288h exit=${code}====="
exit "$code"
