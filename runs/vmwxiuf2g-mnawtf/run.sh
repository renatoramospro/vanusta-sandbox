#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxiuf2g-mnawtf====="
(
  set -e
  python 'run_concurrency.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxiuf2g-mnawtf exit=${code}====="
exit "$code"
