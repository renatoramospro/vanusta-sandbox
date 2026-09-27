#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk43p7b-wz090q====="
(
  set -e
  python 'mvcc_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk43p7b-wz090q exit=${code}====="
exit "$code"
