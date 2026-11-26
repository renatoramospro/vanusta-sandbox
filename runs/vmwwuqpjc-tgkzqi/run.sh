#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwuqpjc-tgkzqi====="
(
  set -e
  python 'broker.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwuqpjc-tgkzqi exit=${code}====="
exit "$code"
