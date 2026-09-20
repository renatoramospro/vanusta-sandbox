#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9n3isi-p7w14b====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9n3isi-p7w14b exit=${code}====="
exit "$code"
