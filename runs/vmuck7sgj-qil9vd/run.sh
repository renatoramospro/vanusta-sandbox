#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuck7sgj-qil9vd====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuck7sgj-qil9vd exit=${code}====="
exit "$code"
