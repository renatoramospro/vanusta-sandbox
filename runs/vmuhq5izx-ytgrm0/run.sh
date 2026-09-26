#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhq5izx-ytgrm0====="
(
  set -e
  python 'scheduler_fixed.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhq5izx-ytgrm0 exit=${code}====="
exit "$code"
