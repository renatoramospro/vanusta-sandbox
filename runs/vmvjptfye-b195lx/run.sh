#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvjptfye-b195lx====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvjptfye-b195lx exit=${code}====="
exit "$code"
