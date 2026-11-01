#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvy6nfh4-hdv5p9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvy6nfh4-hdv5p9 exit=${code}====="
exit "$code"
