#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuce3tky-ixrl6h====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuce3tky-ixrl6h exit=${code}====="
exit "$code"
