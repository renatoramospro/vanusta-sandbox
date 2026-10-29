#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvtvow4z-lfda7r====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvtvow4z-lfda7r exit=${code}====="
exit "$code"
