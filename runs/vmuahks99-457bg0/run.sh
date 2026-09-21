#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuahks99-457bg0====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuahks99-457bg0 exit=${code}====="
exit "$code"
