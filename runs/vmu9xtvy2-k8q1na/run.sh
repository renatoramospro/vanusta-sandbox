#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9xtvy2-k8q1na====="
(
  set -e
  python 'contract_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9xtvy2-k8q1na exit=${code}====="
exit "$code"
