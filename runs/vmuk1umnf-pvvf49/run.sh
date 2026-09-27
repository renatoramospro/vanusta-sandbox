#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk1umnf-pvvf49====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk1umnf-pvvf49 exit=${code}====="
exit "$code"
