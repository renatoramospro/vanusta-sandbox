#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhgeivc-ehemfz====="
(
  set -e
  python 'regex_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhgeivc-ehemfz exit=${code}====="
exit "$code"
