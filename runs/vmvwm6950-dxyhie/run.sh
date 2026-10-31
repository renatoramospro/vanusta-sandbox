#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvwm6950-dxyhie====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvwm6950-dxyhie exit=${code}====="
exit "$code"
