#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmudxen2e-l9hxib====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmudxen2e-l9hxib exit=${code}====="
exit "$code"
