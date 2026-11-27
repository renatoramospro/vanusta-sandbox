#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyc7aw4-bbx5mu====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyc7aw4-bbx5mu exit=${code}====="
exit "$code"
