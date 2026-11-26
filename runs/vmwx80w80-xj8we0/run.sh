#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx80w80-xj8we0====="
(
  set -e
  python 'benchmark_framework_corrected.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx80w80-xj8we0 exit=${code}====="
exit "$code"
