#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukqlrqx-10xdia====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukqlrqx-10xdia exit=${code}====="
exit "$code"
