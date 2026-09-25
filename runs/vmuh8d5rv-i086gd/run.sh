#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh8d5rv-i086gd====="
(
  set -e
  python 'vm.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh8d5rv-i086gd exit=${code}====="
exit "$code"
