#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh8wsbt-8s7cxd====="
(
  set -e
  python 'vm.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh8wsbt-8s7cxd exit=${code}====="
exit "$code"
