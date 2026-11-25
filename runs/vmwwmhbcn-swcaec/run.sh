#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwmhbcn-swcaec====="
(
  set -e
  python 'cfg_builder.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwmhbcn-swcaec exit=${code}====="
exit "$code"
