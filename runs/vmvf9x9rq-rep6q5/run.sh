#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvf9x9rq-rep6q5====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvf9x9rq-rep6q5 exit=${code}====="
exit "$code"
