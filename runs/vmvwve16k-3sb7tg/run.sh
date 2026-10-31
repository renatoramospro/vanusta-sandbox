#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvwve16k-3sb7tg====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvwve16k-3sb7tg exit=${code}====="
exit "$code"
