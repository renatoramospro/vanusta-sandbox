#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmudqz3pe-sv7grq====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmudqz3pe-sv7grq exit=${code}====="
exit "$code"
