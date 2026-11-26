#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxnvuda-ebwn5w====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxnvuda-ebwn5w exit=${code}====="
exit "$code"
