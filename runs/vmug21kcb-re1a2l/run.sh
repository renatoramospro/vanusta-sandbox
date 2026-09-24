#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmug21kcb-re1a2l====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmug21kcb-re1a2l exit=${code}====="
exit "$code"
