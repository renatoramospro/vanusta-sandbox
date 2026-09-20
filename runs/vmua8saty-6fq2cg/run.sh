#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua8saty-6fq2cg====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua8saty-6fq2cg exit=${code}====="
exit "$code"
