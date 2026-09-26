#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuiz9r8j-5lhdlu====="
(
  set -e
  python 'interpreter.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuiz9r8j-5lhdlu exit=${code}====="
exit "$code"
