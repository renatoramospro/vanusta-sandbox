#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuagoegg-tvx30s====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuagoegg-tvx30s exit=${code}====="
exit "$code"
