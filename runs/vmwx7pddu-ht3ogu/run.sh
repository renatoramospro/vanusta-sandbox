#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx7pddu-ht3ogu====="
(
  set -e
  python 'benchmark_framework.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx7pddu-ht3ogu exit=${code}====="
exit "$code"
