#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0bl72y-8of8aw====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0bl72y-8of8aw exit=${code}====="
exit "$code"
