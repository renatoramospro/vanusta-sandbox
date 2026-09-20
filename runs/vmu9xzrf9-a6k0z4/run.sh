#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9xzrf9-a6k0z4====="
(
  set -e
  python 'contract_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9xzrf9-a6k0z4 exit=${code}====="
exit "$code"
