#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuao5xnv-4d3vq2====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuao5xnv-4d3vq2 exit=${code}====="
exit "$code"
