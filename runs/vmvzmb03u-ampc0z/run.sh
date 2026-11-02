#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvzmb03u-ampc0z====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvzmb03u-ampc0z exit=${code}====="
exit "$code"
