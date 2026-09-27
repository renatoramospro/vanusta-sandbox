#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujzducq-27w85p====="
(
  set -e
  python 'minhash_lsh.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujzducq-27w85p exit=${code}====="
exit "$code"
