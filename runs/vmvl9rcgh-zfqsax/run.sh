#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvl9rcgh-zfqsax====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvl9rcgh-zfqsax exit=${code}====="
exit "$code"
