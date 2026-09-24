#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuezvmal-8k7s58====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuezvmal-8k7s58 exit=${code}====="
exit "$code"
