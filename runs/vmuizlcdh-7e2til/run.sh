#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuizlcdh-7e2til====="
(
  set -e
  python 'interpreter.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuizlcdh-7e2til exit=${code}====="
exit "$code"
