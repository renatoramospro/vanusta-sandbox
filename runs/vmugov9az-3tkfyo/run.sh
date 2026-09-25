#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugov9az-3tkfyo====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugov9az-3tkfyo exit=${code}====="
exit "$code"
