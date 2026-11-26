#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwvkwr4-tzqpq0====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwvkwr4-tzqpq0 exit=${code}====="
exit "$code"
