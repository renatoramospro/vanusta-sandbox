#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubqn0cr-tf7vrn====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubqn0cr-tf7vrn exit=${code}====="
exit "$code"
