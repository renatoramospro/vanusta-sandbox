#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuiz223b-ggokni====="
(
  set -e
  python 'interpreter.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuiz223b-ggokni exit=${code}====="
exit "$code"
