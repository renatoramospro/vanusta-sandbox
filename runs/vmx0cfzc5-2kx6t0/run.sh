#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0cfzc5-2kx6t0====="
(
  set -e
  python 'dependency_resolver.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0cfzc5-2kx6t0 exit=${code}====="
exit "$code"
