#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub184jm-696vq2====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub184jm-696vq2 exit=${code}====="
exit "$code"
