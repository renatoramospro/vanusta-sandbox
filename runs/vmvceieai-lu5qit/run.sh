#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvceieai-lu5qit====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvceieai-lu5qit exit=${code}====="
exit "$code"
