#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubntiyo-3cskip====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubntiyo-3cskip exit=${code}====="
exit "$code"
