#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvzbxtr1-fxcg2f====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvzbxtr1-fxcg2f exit=${code}====="
exit "$code"
