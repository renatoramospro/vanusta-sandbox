#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub2g74b-v2qp2g====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub2g74b-v2qp2g exit=${code}====="
exit "$code"
