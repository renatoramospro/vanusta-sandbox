#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucvpit3-9qrj61====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucvpit3-9qrj61 exit=${code}====="
exit "$code"
