#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcx5n2y-ocr8rj====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcx5n2y-ocr8rj exit=${code}====="
exit "$code"
