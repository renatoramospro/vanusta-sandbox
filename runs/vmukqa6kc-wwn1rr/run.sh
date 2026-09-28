#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukqa6kc-wwn1rr====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukqa6kc-wwn1rr exit=${code}====="
exit "$code"
