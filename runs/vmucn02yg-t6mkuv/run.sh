#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucn02yg-t6mkuv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucn02yg-t6mkuv exit=${code}====="
exit "$code"
