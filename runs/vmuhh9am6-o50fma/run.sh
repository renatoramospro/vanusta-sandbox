#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhh9am6-o50fma====="
(
  set -e
  python 'regex_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhh9am6-o50fma exit=${code}====="
exit "$code"
