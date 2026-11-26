#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwufazr-s9jluw====="
(
  set -e
  python 'broker.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwufazr-s9jluw exit=${code}====="
exit "$code"
