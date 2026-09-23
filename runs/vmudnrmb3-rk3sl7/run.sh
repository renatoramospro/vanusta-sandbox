#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmudnrmb3-rk3sl7====="
(
  set -e
  python 'contract_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmudnrmb3-rk3sl7 exit=${code}====="
exit "$code"
