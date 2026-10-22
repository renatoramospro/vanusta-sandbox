#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvk3uzmk-e11ulz====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvk3uzmk-e11ulz exit=${code}====="
exit "$code"
