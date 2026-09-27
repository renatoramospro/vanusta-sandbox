#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukgyjr3-jovgki====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukgyjr3-jovgki exit=${code}====="
exit "$code"
