#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub404jt-353m1c====="
(
  set -e
  python 'pcg_pipeline.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub404jt-353m1c exit=${code}====="
exit "$code"
