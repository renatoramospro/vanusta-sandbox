#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua9icbk-drib7d====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua9icbk-drib7d exit=${code}====="
exit "$code"
