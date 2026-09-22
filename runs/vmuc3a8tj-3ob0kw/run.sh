#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuc3a8tj-3ob0kw====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuc3a8tj-3ob0kw exit=${code}====="
exit "$code"
