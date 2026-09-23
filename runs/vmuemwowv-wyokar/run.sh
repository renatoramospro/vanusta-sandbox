#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuemwowv-wyokar====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuemwowv-wyokar exit=${code}====="
exit "$code"
