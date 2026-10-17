#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcosquq-ds6jw0====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcosquq-ds6jw0 exit=${code}====="
exit "$code"
