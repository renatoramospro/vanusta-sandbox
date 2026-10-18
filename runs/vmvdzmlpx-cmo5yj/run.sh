#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvdzmlpx-cmo5yj====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvdzmlpx-cmo5yj exit=${code}====="
exit "$code"
