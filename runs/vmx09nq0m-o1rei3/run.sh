#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx09nq0m-o1rei3====="
(
  set -e
  python 'simulator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx09nq0m-o1rei3 exit=${code}====="
exit "$code"
