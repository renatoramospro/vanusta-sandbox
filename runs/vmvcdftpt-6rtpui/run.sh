#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcdftpt-6rtpui====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcdftpt-6rtpui exit=${code}====="
exit "$code"
