#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvju7mm0-ljvdoo====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvju7mm0-ljvdoo exit=${code}====="
exit "$code"
