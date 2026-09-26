#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhs2s6d-rxdetp====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhs2s6d-rxdetp exit=${code}====="
exit "$code"
