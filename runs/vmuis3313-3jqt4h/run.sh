#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuis3313-3jqt4h====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuis3313-3jqt4h exit=${code}====="
exit "$code"
