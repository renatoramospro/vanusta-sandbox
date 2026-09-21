#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubkuo5r-u7ds2r====="
(
  set -e
  python 'cache_system_v2.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubkuo5r-u7ds2r exit=${code}====="
exit "$code"
