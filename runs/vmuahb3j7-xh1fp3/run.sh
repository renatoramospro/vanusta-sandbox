#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuahb3j7-xh1fp3====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuahb3j7-xh1fp3 exit=${code}====="
exit "$code"
