#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwvemzwo-ku4qxo====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwvemzwo-ku4qxo exit=${code}====="
exit "$code"
