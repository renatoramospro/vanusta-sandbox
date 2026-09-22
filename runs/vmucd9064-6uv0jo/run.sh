#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucd9064-6uv0jo====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucd9064-6uv0jo exit=${code}====="
exit "$code"
