#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwsl4we-jujs7s====="
(
  set -e
  python 'benchmark.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwsl4we-jujs7s exit=${code}====="
exit "$code"
