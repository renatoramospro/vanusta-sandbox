#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuah0d2v-twejj3====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuah0d2v-twejj3 exit=${code}====="
exit "$code"
