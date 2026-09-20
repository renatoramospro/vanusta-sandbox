#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9pk1io-39plkn====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9pk1io-39plkn exit=${code}====="
exit "$code"
