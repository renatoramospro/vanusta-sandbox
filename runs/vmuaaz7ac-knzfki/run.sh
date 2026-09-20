#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuaaz7ac-knzfki====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuaaz7ac-knzfki exit=${code}====="
exit "$code"
