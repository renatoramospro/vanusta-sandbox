#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubpbveh-w5lras====="
(
  set -e
  python 'gitops_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubpbveh-w5lras exit=${code}====="
exit "$code"
