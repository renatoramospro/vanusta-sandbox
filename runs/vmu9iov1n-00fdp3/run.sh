#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9iov1n-00fdp3====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9iov1n-00fdp3 exit=${code}====="
exit "$code"
