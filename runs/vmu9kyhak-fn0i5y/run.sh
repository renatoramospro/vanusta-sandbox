#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9kyhak-fn0i5y====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9kyhak-fn0i5y exit=${code}====="
exit "$code"
